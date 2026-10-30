from datetime import date

import flet as ft

from budget import month_records, totals


def _money(value):
    return f"¥{value:,.2f}"


def build(page: ft.Page, store):
    today = date.today()
    month = today.strftime("%Y-%m")
    records = month_records(store, month)
    income, expense, balance = totals(records)
    budget = store.get_budget(month)
    ratio = min(expense / budget, 1.0) if budget > 0 else 0.0
    today_records = [r for r in records if r["entry_date"] == today.isoformat()]
    today_meals = {r["meal"] for r in today_records if r["kind"] == "支出" and r["meal"]}
    recent = store.transactions(end=today.isoformat())[:6]
    icons = {c["name"]: c["icon"] for c in store.list_categories()}

    summary = ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text(today.strftime("%Y年%m月收支"), size=16),
                ft.Text(_money(balance), size=30, weight=ft.FontWeight.BOLD),
                ft.Text("本月结余"),
                ft.Row([
                    ft.Column([ft.Text("收入"), ft.Text(_money(income), color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)]),
                    ft.Column([ft.Text("支出"), ft.Text(_money(expense), color=ft.Colors.RED, weight=ft.FontWeight.BOLD)]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=20,
        )
    )

    budget_text = f"已支出 {_money(expense)} / 预算 {_money(budget)}" if budget else f"本月已支出 {_money(expense)}，尚未设置预算"
    budget_card = ft.Card(content=ft.Container(content=ft.Column([
        ft.Row([ft.Text("月度预算", weight=ft.FontWeight.BOLD), ft.Text(f"{ratio:.0%}" if budget else "未设置")],
                 alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text(budget_text),
        ft.ProgressBar(value=ratio, color=ft.Colors.TEAL),
    ]), padding=16))

    meal_card = ft.Card(content=ft.Container(content=ft.Column([
        ft.Text("今日三餐", size=18, weight=ft.FontWeight.BOLD),
        ft.Text(" · ".join(f"{meal}{' ✓' if meal in today_meals else ' ○'}" for meal in ["早餐", "午餐", "晚餐"])),
        ft.Text(f"今日记录 {len(today_records)} 笔"),
    ]), padding=16))

    recent_controls = [ft.Text("最近记录", size=18, weight=ft.FontWeight.BOLD)]
    if not recent:
        recent_controls.append(ft.Text("还没有账目，点右下角 + 开始记录今天的收支。"))
    for item in recent:
        recent_controls.append(ft.ListTile(
            leading=ft.Icon(getattr(ft.Icons, icons.get(item["category"], "CATEGORY"), ft.Icons.CATEGORY)),
            title=ft.Text(item["category"] + (f" · {item['meal']}" if item.get("meal") else "")),
            subtitle=ft.Text(f"{item['entry_date']}  {item.get('note') or item.get('merchant') or item.get('payment') or ''}"),
            trailing=ft.Text(("+" if item["kind"] == "收入" else "−") + _money(item["amount"]),
                             color=ft.Colors.GREEN if item["kind"] == "收入" else ft.Colors.RED),
        ))

    return ft.Column([
        ft.Text("今天，记得好好生活。", size=16),
        summary,
        budget_card,
        meal_card,
        *recent_controls,
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
