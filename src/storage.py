import json
import sqlite3
from datetime import date

from data import ALL_CATEGORIES


class LedgerStore:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.connection.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('支出', '收入')),
                icon TEXT NOT NULL DEFAULT 'CATEGORY',
                UNIQUE(name, kind)
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                kind TEXT NOT NULL CHECK(kind IN ('支出', '收入')),
                category TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                meal TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                payment TEXT NOT NULL DEFAULT '',
                merchant TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(entry_date);
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '全部支出',
                amount REAL NOT NULL CHECK(amount >= 0),
                UNIQUE(month, category)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        for name, kind, icon in ALL_CATEGORIES:
            self.connection.execute(
                "INSERT OR IGNORE INTO categories(name, kind, icon) VALUES (?, ?, ?)",
                (name, kind, icon),
            )
        self.connection.commit()

    def list_categories(self, kind: str | None = None):
        if kind:
            rows = self.connection.execute(
                "SELECT name, kind, icon FROM categories WHERE kind=? ORDER BY id", (kind,)
            )
        else:
            rows = self.connection.execute("SELECT name, kind, icon FROM categories ORDER BY id")
        return [dict(row) for row in rows.fetchall()]

    def add_category(self, name: str, kind: str, icon: str = "CATEGORY"):
        self.connection.execute(
            "INSERT INTO categories(name, kind, icon) VALUES (?, ?, ?)", (name, kind, icon)
        )
        self.connection.commit()

    def add_transaction(self, record: dict):
        self.connection.execute(
            """INSERT INTO transactions
            (amount, kind, category, entry_date, meal, note, payment, merchant)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["amount"], record["kind"], record["category"], record["entry_date"],
             record.get("meal", ""), record.get("note", ""), record.get("payment", ""),
             record.get("merchant", "")),
        )
        self.connection.commit()

    def update_transaction(self, record_id: int, record: dict):
        self.connection.execute(
            """UPDATE transactions SET amount=?, kind=?, category=?, entry_date=?, meal=?,
            note=?, payment=?, merchant=? WHERE id=?""",
            (record["amount"], record["kind"], record["category"], record["entry_date"],
             record.get("meal", ""), record.get("note", ""), record.get("payment", ""),
             record.get("merchant", ""), record_id),
        )
        self.connection.commit()

    def delete_transaction(self, record_id: int):
        self.connection.execute("DELETE FROM transactions WHERE id=?", (record_id,))
        self.connection.commit()

    def get_transaction(self, record_id: int):
        row = self.connection.execute("SELECT * FROM transactions WHERE id=?", (record_id,)).fetchone()
        return dict(row) if row else None

    def transaction_months(self):
        rows = self.connection.execute(
            "SELECT DISTINCT substr(entry_date, 1, 7) AS month FROM transactions ORDER BY month DESC"
        )
        return [row["month"] for row in rows.fetchall()]

    def transactions(self, start: str | None = None, end: str | None = None, kind: str | None = None):
        clauses, params = [], []
        if start:
            clauses.append("entry_date >= ?")
            params.append(start)
        if end:
            clauses.append("entry_date <= ?")
            params.append(end)
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.connection.execute(
            "SELECT * FROM transactions" + where + " ORDER BY entry_date DESC, id DESC", params
        )
        return [dict(row) for row in rows.fetchall()]

    def get_budget(self, month: str, category: str = "全部支出"):
        row = self.connection.execute(
            "SELECT amount FROM budgets WHERE month=? AND category=?", (month, category)
        ).fetchone()
        return float(row["amount"]) if row else 0.0

    def set_budget(self, month: str, amount: float, category: str = "全部支出"):
        self.connection.execute(
            """INSERT INTO budgets(month, category, amount) VALUES (?, ?, ?)
            ON CONFLICT(month, category) DO UPDATE SET amount=excluded.amount""",
            (month, category, amount),
        )
        self.connection.commit()

    def get_setting(self, key: str, default: str = ""):
        row = self.connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        self.connection.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )
        self.connection.commit()

    def export_backup(self):
        tables = {
            "categories": "SELECT * FROM categories ORDER BY id",
            "transactions": "SELECT * FROM transactions ORDER BY id",
            "budgets": "SELECT * FROM budgets ORDER BY id",
            "settings": "SELECT * FROM settings ORDER BY key",
        }
        data = {name: [dict(row) for row in self.connection.execute(query).fetchall()]
                for name, query in tables.items()}
        return {"format": "daily-ledger-backup", "schema_version": 1, **data}

    def import_backup(self, backup):
        if not isinstance(backup, dict) or backup.get("format") != "daily-ledger-backup":
            raise ValueError("这不是每日账本的备份文件。")
        if backup.get("schema_version") != 1:
            raise ValueError("备份文件版本不受支持。")

        raw_categories = backup.get("categories")
        raw_transactions = backup.get("transactions")
        raw_budgets = backup.get("budgets")
        raw_settings = backup.get("settings")
        if not all(isinstance(value, list) for value in [raw_categories, raw_transactions, raw_budgets]):
            raise ValueError("备份文件内容不完整。")
        if not isinstance(raw_settings, list):
            raise ValueError("备份文件中的界面设置无效。")

        categories = []
        for item in raw_categories:
            if not isinstance(item, dict):
                raise ValueError("分类数据格式无效。")
            name, kind = str(item.get("name", "")).strip(), item.get("kind")
            if not name or kind not in ("支出", "收入"):
                raise ValueError("备份中存在无效分类。")
            categories.append({"id": item.get("id"), "name": name, "kind": kind,
                               "icon": str(item.get("icon", "CATEGORY"))})

        transactions = []
        for item in raw_transactions:
            if not isinstance(item, dict):
                raise ValueError("账目数据格式无效。")
            kind = item.get("kind")
            category = str(item.get("category", "")).strip()
            try:
                amount = float(item.get("amount"))
                entry_date = date.fromisoformat(str(item.get("entry_date", ""))).isoformat()
            except (TypeError, ValueError):
                raise ValueError("备份中存在无效金额或日期。") from None
            if amount <= 0 or kind not in ("支出", "收入") or not category:
                raise ValueError("备份中存在无效账目。")
            transactions.append({
                "id": item.get("id"), "amount": amount, "kind": kind, "category": category,
                "entry_date": entry_date, "meal": str(item.get("meal", "")),
                "note": str(item.get("note", "")), "payment": str(item.get("payment", "")),
                "merchant": str(item.get("merchant", "")),
                "created_at": str(item.get("created_at", "")),
            })

        budgets = []
        for item in raw_budgets:
            if not isinstance(item, dict):
                raise ValueError("预算数据格式无效。")
            month = str(item.get("month", ""))
            try:
                date.fromisoformat(month + "-01")
                amount = float(item.get("amount"))
            except (TypeError, ValueError):
                raise ValueError("备份中存在无效预算。") from None
            if amount < 0:
                raise ValueError("备份中存在无效预算金额。")
            budgets.append({"id": item.get("id"), "month": month,
                            "category": str(item.get("category", "全部支出")), "amount": amount})

        settings = []
        for item in raw_settings:
            if not isinstance(item, dict) or "key" not in item or "value" not in item:
                raise ValueError("界面设置数据格式无效。")
            settings.append({"key": str(item["key"]), "value": str(item["value"])})

        with self.connection:
            self.connection.execute("DELETE FROM transactions")
            self.connection.execute("DELETE FROM budgets")
            self.connection.execute("DELETE FROM categories")
            self.connection.execute("DELETE FROM settings")
            for item in categories:
                category_id = item["id"]
                if isinstance(category_id, int) and category_id > 0:
                    self.connection.execute(
                        "INSERT INTO categories(id, name, kind, icon) VALUES (?, ?, ?, ?)",
                        (category_id, item["name"], item["kind"], item["icon"]),
                    )
                else:
                    self.connection.execute(
                        "INSERT INTO categories(name, kind, icon) VALUES (?, ?, ?)",
                        (item["name"], item["kind"], item["icon"]),
                    )
            for name, kind, icon in ALL_CATEGORIES:
                self.connection.execute(
                    "INSERT OR IGNORE INTO categories(name, kind, icon) VALUES (?, ?, ?)",
                    (name, kind, icon),
                )
            for item in transactions:
                if isinstance(item["id"], int) and item["id"] > 0:
                    self.connection.execute(
                        """INSERT INTO transactions
                        (id, amount, kind, category, entry_date, meal, note, payment, merchant, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_TIMESTAMP))""",
                        (item["id"], item["amount"], item["kind"], item["category"], item["entry_date"],
                         item["meal"], item["note"], item["payment"], item["merchant"], item["created_at"]),
                    )
                else:
                    self.connection.execute(
                        """INSERT INTO transactions
                        (amount, kind, category, entry_date, meal, note, payment, merchant)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (item["amount"], item["kind"], item["category"], item["entry_date"],
                         item["meal"], item["note"], item["payment"], item["merchant"]),
                    )
            for item in budgets:
                self.connection.execute(
                    "INSERT INTO budgets(month, category, amount) VALUES (?, ?, ?)",
                    (item["month"], item["category"], item["amount"]),
                )
            for item in settings:
                self.connection.execute(
                    "INSERT INTO settings(key, value) VALUES (?, ?)", (item["key"], item["value"])
                )

    def close(self):
        self.connection.close()
