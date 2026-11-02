from datetime import date

import flet as ft
from flet_charts import PieChart, PieChartSection

from budget import category_totals, month_records, totals
from views.ledger import open_editor
from theme import input_control_style

CHART_COLORS = [
    ft.Colors.TEAL, ft.Colors.BLUE, ft.Colors.DEEP_ORANGE, ft.Colors.PURPLE,
    ft.Colors.GREEN, ft.Colors.PINK, ft.Colors.AMBER, ft.Colors.INDIGO,
    ft.Colors.LIGHT_BLUE_700, ft.Colors.LIME_700, ft.Colors.BROWN, ft.Colors.CYAN_700,
    ft.Colors.RED, ft.Colors.DEEP_PURPLE, ft.Colors.ORANGE, ft.Colors.BLUE_GREY,
    ft.Colors.LIGHT_GREEN_700, ft.Colors.YELLOW_800, ft.Colors.TEAL_700, ft.Colors.PURPLE_300,
]


def _money(value):
    return f"¥{value:,.2f}"


def _options(names):
    return [ft.DropdownOption(key=name, text=name) for name in names]


def _month_label(month):
    year, number = month.split("-")
    return f"{year}年{int(number)}月"


def _shift_month(month, offset):
    year, number = map(int, month.split("-"))
    serial = year * 12 + number - 1 + offset
    return f"{serial // 12:04d}-{serial % 12 + 1:02d}"


def _open_budget_dialog(page, store, month, categories, on_changed):
    category = ft.Dropdown(
        **input_control_style(), label="预算范围", value="全部支出",
        options=_options(["全部支出"] + categories),
    )
    amount = ft.TextField(
        **input_control_style(), label="本月预算（元）", keyboard_type=ft.KeyboardType.NUMBER,
    )
    error = ft.Text("", color=ft.Colors.RED)

    def save():
        try:
            value = float((amount.value or "").strip())
            if value < 0:
                raise ValueError
        except ValueError:
            error.value = "请输入不小于 0 的预算金额。"
            page.update()
            return
        store.set_budget(month, value, category.value or "全部支出")
        page.pop_dialog()
        on_changed()

    page.show_dialog(ft.AlertDialog(
        modal=True, title=ft.Text("设置月度预算"),
        content=ft.Column([category, amount, error], tight=True),
        actions=[ft.TextButton(content="取消", on_click=lambda: page.pop_dialog()), ft.Button(content="保存", on_click=save)],
    ))


def _open_category_dialog(page, store, on_changed):
    kind = ft.Dropdown(
        **input_control_style(), label="类型", value="支出", options=_options(["支出", "收入"]),
    )
    name = ft.TextField(**input_control_style(), label="新分类名称")
    error = ft.Text("", color=ft.Colors.RED)

    def save():
        value = (name.value or "").strip()
        if not value:
            error.value = "请填写分类名称。"
            page.update()
            return
        try:
            store.add_category(value, kind.value or "支出")
        except Exception:
            error.value = "该分类已存在，请换一个名称。"
            page.update()
            return
        page.pop_dialog()
        on_changed()

    page.show_dialog(ft.AlertDialog(
        modal=True, title=ft.Text("添加自定义分类"),
        content=ft.Column([kind, name, error], tight=True),
        actions=[ft.TextButton(content="取消", on_click=lambda: page.pop_dialog()), ft.Button(content="添加", on_click=save)],
    ))


def build(page: ft.Page, store, on_changed):
    current_month = date.today().strftime("%Y-%m")
    recorded_months = store.transaction_months()
    available_months = sorted(set(recorded_months + [current_month]), reverse=True)
    month = store.get_setting("reports_selected_month", current_month)
    try:
        date.fromisoformat(month + "-01")
        valid_month = len(month) == 7 and month <= current_month
    except ValueError:
        valid_month = False
    if not valid_month:
        month = current_month
        store.set_setting("reports_selected_month", month)
    if month not in available_months:
        available_months.append(month)
        available_months.sort(reverse=True)

    def select_month(value):
        store.set_setting("reports_selected_month", value)
        on_changed()

    def choose_month(e):
        if e.control.value:
            select_month(e.control.value)

    def shift_month(offset):
        target = _shift_month(month, offset)
        if target <= current_month:
            select_month(target)

    records = month_records(store, month)
    income, expense, balance = totals(records)
    categories = store.list_categories()
    expense_names = [item["name"] for item in categories if item["kind"] == "支出"]
    budget = store.get_budget(month)
    ratio = min(expense / budget, 1.0) if budget else 0.0
    category_rows = category_totals(records, "支出")
    income_rows = category_totals(records, "收入")

    budget_card = ft.Card(content=ft.Container(content=ft.Column([
        ft.Row([ft.Text("总预算", weight=ft.FontWeight.BOLD), ft.Button(content="设置预算", on_click=lambda: _open_budget_dialog(page, store, month, expense_names, on_changed))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text(f"已支出 {_money(expense)} / 预算 {_money(budget)}" if budget else f"本月支出 {_money(expense)}，尚未设置总预算"),
        ft.ProgressBar(value=ratio, color=ft.Colors.TEAL),
        ft.Text(f"剩余 {_money(max(budget - expense, 0))}" if budget else "可设置总预算或单项分类预算"),
    ]), padding=16))

    ranked = [ft.Text("支出分类排行", size=18, weight=ft.FontWeight.BOLD)]
    if category_rows:
        sections = [
            PieChartSection(value=value, color=CHART_COLORS[index % len(CHART_COLORS)], radius=100)
            for index, (_, value) in enumerate(category_rows)
        ]
        ranked.append(ft.Row(
            [PieChart(sections=sections, width=240, height=240, sections_space=2, center_space_radius=0)],
            alignment=ft.MainAxisAlignment.CENTER,
        ))
        for index, (name, value) in enumerate(category_rows):
            color = CHART_COLORS[index % len(CHART_COLORS)]
            share = value / expense if expense else 0
            ranked.append(ft.Row([
                ft.Container(width=14, height=14, bgcolor=color, border_radius=7),
                ft.Text(name, expand=True), ft.Text(_money(value)), ft.Text(f"{share:.1%}"),
            ], spacing=10))
    else:
        ranked.append(ft.Text("本月暂无支出分类统计。"))
    pie_card = ft.Card(content=ft.Container(content=ft.Column(ranked, spacing=10), padding=14))

    summary_rows = [ft.Text("分类汇总", size=18, weight=ft.FontWeight.BOLD)]
    for label, rows, color in (("支出", category_rows, ft.Colors.RED), ("收入", income_rows, ft.Colors.GREEN)):
        summary_rows.append(ft.Text(label, weight=ft.FontWeight.BOLD, color=color))
        if rows:
            for name, amount in rows:
                summary_rows.append(ft.Row([ft.Text(name, expand=True), ft.Text(_money(amount))]))
        else:
            summary_rows.append(ft.Text("暂无记录"))
    category_summary = ft.Card(content=ft.Container(content=ft.Column(summary_rows, spacing=8), padding=14))

    detail_rows = [ft.Text(f"记账明细（{len(records)}笔）", size=18, weight=ft.FontWeight.BOLD)]
    if records:
        for record in records:
            sign = "−" if record["kind"] == "支出" else "+"
            color = ft.Colors.RED if record["kind"] == "支出" else ft.Colors.GREEN
            subtitle = " · ".join(part for part in [record.get("merchant", ""), record.get("note", ""), record.get("payment", "")] if part)
            detail_rows.append(ft.ListTile(
                title=ft.Text(f"{record['category']}  ·  {record['entry_date']}"),
                subtitle=ft.Text(subtitle or record["kind"]),
                trailing=ft.Text(f"{sign}{_money(record['amount'])}", color=color, weight=ft.FontWeight.BOLD),
                on_click=lambda e, item=record: open_editor(page, store, on_changed, item),
            ))
    else:
        detail_rows.append(ft.Text("这个月还没有记账记录。"))
    details_card = ft.Card(content=ft.Container(content=ft.Column(detail_rows, spacing=4), padding=14))

    category_section = ft.Card(content=ft.Container(content=ft.Column([
        ft.Row([ft.Text("分类管理", size=18, weight=ft.FontWeight.BOLD),
                ft.TextButton(content="＋ 添加分类", on_click=lambda: _open_category_dialog(page, store, on_changed))],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Text(f"支出 {len(expense_names)} 类 · 收入 {len(categories) - len(expense_names)} 类"),
        ft.Text("内置餐饮、住房、水电、交通、医疗、教育、旅行、娱乐、工资、退款等分类，可添加自定义分类。"),
    ]), padding=14))

    month_selector = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[ft.Container(
            width=276,
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.TEAL),
            border_radius=ft.BorderRadius.all(18),
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH, size=17, color=ft.Colors.TEAL_700),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_LEFT, tooltip="上个月", width=32, height=32,
                        icon_size=18, padding=0, on_click=lambda: shift_month(-1),
                    ),
                    ft.Dropdown(
                        value=month, options=_options(available_months), on_select=choose_month,
                        width=142, dense=True, text_size=14,
                        content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
                        filled=True, fill_color=ft.Colors.with_opacity(0.12, ft.Colors.TEAL),
                        border=ft.OutlineInputBorder(border_radius=ft.BorderRadius.all(12)),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHEVRON_RIGHT, tooltip="下个月", width=32, height=32,
                        icon_size=18, padding=0, disabled=month >= current_month,
                        on_click=lambda: shift_month(1),
                    ),
                ],
            ),
        )],
    )

    return ft.Column([
        ft.Text("月度分析", size=24, weight=ft.FontWeight.BOLD),
        month_selector,
        ft.Card(content=ft.Container(content=ft.Row([
            ft.Column([ft.Text("收入"), ft.Text(_money(income), color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD)]),
            ft.Column([ft.Text("支出"), ft.Text(_money(expense), color=ft.Colors.RED, weight=ft.FontWeight.BOLD)]),
            ft.Column([ft.Text("结余"), ft.Text(_money(balance), weight=ft.FontWeight.BOLD)]),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=16)),
        budget_card, pie_card, category_summary, details_card, category_section,
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
