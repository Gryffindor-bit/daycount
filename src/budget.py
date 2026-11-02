from calendar import monthrange
from datetime import date, timedelta


def month_bounds(month: str):
    year, number = map(int, month.split("-"))
    last = monthrange(year, number)[1]
    return f"{month}-01", f"{month}-{last:02d}"


def month_records(store, month: str):
    start, end = month_bounds(month)
    return store.transactions(start, end)


def totals(records):
    income = sum(r["amount"] for r in records if r["kind"] == "收入")
    expense = sum(r["amount"] for r in records if r["kind"] == "支出")
    return income, expense, income - expense


def daily_totals(records):
    result = {}
    for item in records:
        day = item["entry_date"]
        result.setdefault(day, {"收入": 0.0, "支出": 0.0})
        result[day][item["kind"]] += item["amount"]
    return result


def category_totals(records, kind="支出"):
    result = {}
    for item in records:
        if item["kind"] == kind:
            result[item["category"]] = result.get(item["category"], 0.0) + item["amount"]
    return sorted(result.items(), key=lambda pair: pair[1], reverse=True)


def calendar_grid(year: int, month: int):
    first = date(year, month, 1)
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    return [start + timedelta(days=i) for i in range(42)]
