import sqlite3
from datetime import date
from pathlib import Path

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

    def close(self):
        self.connection.close()
