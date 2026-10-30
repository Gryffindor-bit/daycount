import calendar
from datetime import date

import flet as ft

from budget import calendar_grid, daily_totals


def _money(value):
    return f"¥{value:,.2f}"


def build(page: ft.Page, store):
    today = date.today()
    state = {"year": today.year, "month": today.month, "selected": today.isoformat()}
    root = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

    def redraw(update_page=False):
        year, month = state["year"], state["month"]
        month_key = f"{year:04d}-{month:02d}"
        _, last_day = calendar.monthrange(year, month)
        records = store.transactions(f"{month_key}-01", f"{month_key}-{last_day:02d}")
        totals = daily_totals(records)
        selected_records = [r for r in records if r["entry_date"] == state["selected"]]
        month_title = f"{year}年{month:02d}月"
        weekday_header = ft.Row([ft.Container(content=ft.Text(day, text_align=ft.TextAlign.CENTER), expand=True)
                                 for day in ["日", "一", "二", "三", "四", "五", "六"]])
        cells = []
        for day in calendar_grid(year, month):
            in_month = day.month == month
            key = day.isoformat()
            sums = totals.get(key, {})
            selected = key == state["selected"]
            label = str(day.day)
            if sums:
                label += "\n" + (f"−{sums['支出']:.0f}" if sums["支出"] else f"+{sums['收入']:.0f}")
            cells.append(ft.Container(
                content=ft.Text(label, size=11, text_align=ft.TextAlign.CENTER,
                                 color=ft.Colors.WHITE if selected else (ft.Colors.BLUE_GREY if in_month else ft.Colors.GREY)),
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TEAL if selected else (ft.Colors.TEAL_50 if key in totals else None),
                border_radius=8,
                on_click=lambda e, picked=key: choose_day(picked),
            ))
        grid = ft.GridView(controls=cells, max_extent=52, child_aspect_ratio=0.9, spacing=4, run_spacing=4, height=310)
        icons = {c["name"]: c["icon"] for c in store.list_categories()}
        selected_sum = totals.get(state["selected"], {"收入": 0.0, "支出": 0.0})
        detail = [
            ft.Text(f"{state['selected']}  ·  收入 {_money(selected_sum['收入'])}  ·  支出 {_money(selected_sum['支出'])}",
                    size=16, weight=ft.FontWeight.BOLD)
        ]
        if not selected_records:
            detail.append(ft.Text("这一天还没有记录。"))
        for item in selected_records:
            desc = " · ".join(part for part in [item.get("meal"), item.get("merchant"), item.get("note")] if part)
            detail.append(ft.ListTile(
                leading=ft.Icon(getattr(ft.Icons, icons.get(item["category"], "CATEGORY"), ft.Icons.CATEGORY)),
                title=ft.Text(item["category"] + (f" · {item['meal']}" if item.get("meal") else "")),
                subtitle=ft.Text(desc or item.get("payment", "")),
                trailing=ft.Text(("+" if item["kind"] == "收入" else "−") + _money(item["amount"]),
                                 color=ft.Colors.GREEN if item["kind"] == "收入" else ft.Colors.RED),
            ))
        root.controls = [
            ft.Text("收支日历", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.TextButton(content="‹ 上月", on_click=lambda: shift_month(-1)),
                ft.Text(month_title, size=18, weight=ft.FontWeight.BOLD),
                ft.TextButton(content="下月 ›", on_click=lambda: shift_month(1)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            weekday_header,
            grid,
            ft.Divider(),
            *detail,
        ]
        if update_page:
            page.update()

    def choose_day(key):
        state["selected"] = key
        redraw(True)

    def shift_month(offset):
        year, month = state["year"], state["month"] + offset
        if month < 1:
            year, month = year - 1, 12
        elif month > 12:
            year, month = year + 1, 1
        state["year"], state["month"] = year, month
        state["selected"] = f"{year:04d}-{month:02d}-01"
        redraw(True)

    # Build initial controls without calling update until the view is mounted.
    redraw()
    return root
