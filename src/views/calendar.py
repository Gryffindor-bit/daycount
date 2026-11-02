import calendar
import math
from datetime import date

import flet as ft
from flet_charts import (
    ChartAxis,
    ChartAxisLabel,
    ChartGridLines,
    LineChart,
    LineChartData,
    LineChartDataPoint,
)

from budget import calendar_grid, daily_totals

INCOME_COLOR = ft.Colors.GREEN_600
EXPENSE_COLOR = ft.Colors.DEEP_ORANGE_600
BALANCE_COLOR = ft.Colors.BLUE_600


def _money(value):
    return f"¥{value:,.2f}"


def _month_index(month):
    year, number = map(int, month.split("-"))
    return year * 12 + number - 1


def _month_from_index(index):
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _month_label(month):
    year, number = month.split("-")
    return f"{year}年{int(number)}月"


def _month_options(months):
    return [ft.DropdownOption(key=month, text=_month_label(month)) for month in months]


def _axis_money(value):
    if abs(value) >= 10000:
        label = f"¥{value / 10000:.1f}万"
        return label.replace(".0万", "万")
    return f"¥{value:,.0f}"


def _chart_y_bounds(values):
    low, high = min([0.0, *values]), max([0.0, *values])
    raw_step = (high - low) / 4 if high != low else 1.0
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = math.ceil(raw_step / magnitude) * magnitude
    min_y = math.floor(low / step) * step
    max_y = math.ceil(high / step) * step
    if min_y == max_y:
        max_y = min_y + step
    labels = []
    current = min_y
    while current <= max_y + step * 0.001:
        labels.append(ChartAxisLabel(value=current, label=_axis_money(current)))
        current += step
    return min_y, max_y, step, labels


def build(page: ft.Page, store):
    today = date.today()
    current_month = today.strftime("%Y-%m")
    history_months = store.transaction_months()
    earliest = min(history_months) if history_months else current_month
    earliest_index = min(_month_index(earliest), _month_index(current_month) - 11)
    all_chart_months = [
        _month_from_index(index)
        for index in range(earliest_index, _month_index(current_month) + 1)
    ]
    latest_index = _month_index(current_month)
    default_start = _month_from_index(latest_index - 5)
    saved_start = store.get_setting("calendar_chart_start", default_start)
    saved_end = store.get_setting("calendar_chart_end", current_month)
    try:
        date.fromisoformat(saved_start + "-01")
        date.fromisoformat(saved_end + "-01")
        start_index = _month_index(saved_start)
        end_index = _month_index(saved_end)
        saved_range_valid = (
            len(saved_start) == 7 and len(saved_end) == 7
            and earliest_index <= start_index < end_index <= latest_index
            and 1 <= end_index - start_index <= 11
        )
    except (TypeError, ValueError):
        saved_range_valid = False
    chart_state = {
        "start": saved_start if saved_range_valid else default_start,
        "end": saved_end if saved_range_valid else current_month,
        "show_income": store.get_setting("calendar_chart_show_income", "1") == "1",
        "show_expense": store.get_setting("calendar_chart_show_expense", "1") == "1",
        "show_balance": store.get_setting("calendar_chart_show_balance", "1") == "1",
    }
    if not any(chart_state[key] for key in ("show_income", "show_expense", "show_balance")):
        chart_state["show_income"] = True
    state = {"year": today.year, "month": today.month, "selected": today.isoformat()}
    root = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)

    def redraw(update_page=False):
        year, month = state["year"], state["month"]
        month_key = f"{year:04d}-{month:02d}"
        _, last_day = calendar.monthrange(year, month)
        records = store.transactions(f"{month_key}-01", f"{month_key}-{last_day:02d}")
        day_totals = daily_totals(records)
        selected_records = [r for r in records if r["entry_date"] == state["selected"]]
        month_title = f"{year}年{month:02d}月"
        weekday_header = ft.Row([
            ft.Container(content=ft.Text(day, text_align=ft.TextAlign.CENTER), expand=True)
            for day in ["日", "一", "二", "三", "四", "五", "六"]
        ])
        cells = []
        for day in calendar_grid(year, month):
            in_month = day.month == month
            key = day.isoformat()
            sums = day_totals.get(key, {})
            selected = key == state["selected"]
            label = str(day.day)
            if sums:
                label += "\n" + (f"−{sums['支出']:.0f}" if sums["支出"] else f"+{sums['收入']:.0f}")
            cells.append(ft.Container(
                content=ft.Text(label, size=11, text_align=ft.TextAlign.CENTER,
                                 color=ft.Colors.WHITE if selected else (ft.Colors.BLUE_GREY if in_month else ft.Colors.GREY)),
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.TEAL if selected else (ft.Colors.TEAL_50 if key in day_totals else None),
                border_radius=8,
                on_click=lambda e, picked=key: choose_day(picked),
            ))
        grid = ft.GridView(controls=cells, max_extent=52, child_aspect_ratio=0.9, spacing=4, run_spacing=4, height=310)
        icons = {c["name"]: c["icon"] for c in store.list_categories()}
        selected_sum = day_totals.get(state["selected"], {"收入": 0.0, "支出": 0.0})
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

        start_index = _month_index(chart_state["start"])
        end_index = _month_index(chart_state["end"])
        start_candidates = [
            item for item in all_chart_months
            if end_index - 11 <= _month_index(item) <= end_index - 1
        ]
        end_candidates = [
            item for item in all_chart_months
            if start_index + 1 <= _month_index(item) <= min(start_index + 11, latest_index)
        ]

        def choose_chart_start(e):
            selected = e.control.value
            if not selected:
                return
            chart_state["start"] = selected
            store.set_setting("calendar_chart_start", selected)
            redraw(True)

        def choose_chart_end(e):
            selected = e.control.value
            if not selected:
                return
            chart_state["end"] = selected
            store.set_setting("calendar_chart_end", selected)
            redraw(True)

        chart_months = [
            _month_from_index(index)
            for index in range(start_index, end_index + 1)
        ]
        range_start = f"{chart_months[0]}-01"
        range_end = f"{chart_months[-1]}-{calendar.monthrange(*map(int, chart_months[-1].split('-')))[1]:02d}"
        range_records = store.transactions(range_start, range_end)
        monthly = {item: {"收入": 0.0, "支出": 0.0} for item in chart_months}
        for item in range_records:
            monthly[item["entry_date"][:7]][item["kind"]] += item["amount"]
        income_values = [monthly[item]["收入"] for item in chart_months]
        expense_values = [monthly[item]["支出"] for item in chart_months]
        balance_values = [income - expense for income, expense in zip(income_values, expense_values)]
        all_values = income_values + expense_values + balance_values
        min_y, max_y, y_step, y_labels = _chart_y_bounds(all_values)
        x_labels = [
            ChartAxisLabel(value=index, label=f"{item[-2:]}月")
            for index, item in enumerate(chart_months)
        ]

        def series(name, color, values):
            return LineChartData(
                points=[
                    LineChartDataPoint(x=index, y=value, tooltip=f"{_month_label(chart_months[index])} · {name} {_money(value)}")
                    for index, value in enumerate(values)
                ],
                color=color,
                curved=True,
                prevent_curve_over_shooting=True,
                stroke_width=3,
                rounded_stroke_cap=True,
                point=True,
                selected_point=True,
            )

        series_config = [
            ("收入", "show_income", "calendar_chart_show_income", INCOME_COLOR, income_values),
            ("支出", "show_expense", "calendar_chart_show_expense", EXPENSE_COLOR, expense_values),
            ("结余", "show_balance", "calendar_chart_show_balance", BALANCE_COLOR, balance_values),
        ]

        def toggle_series(e, state_key, setting_key):
            if not e.control.value and sum(chart_state[key] for _, key, _, _, _ in series_config) <= 1:
                e.control.value = True
                page.update()
                return
            chart_state[state_key] = bool(e.control.value)
            store.set_setting(setting_key, "1" if e.control.value else "0")
            redraw(True)

        month_width = max(112, min(145, ((page.width or 360) - 100) / 2))
        selectors = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            controls=[
                ft.Dropdown(
                    label="开始", value=chart_state["start"], options=_month_options(start_candidates),
                    on_select=choose_chart_start, width=month_width, height=48, dense=True, text_size=13,
                    content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
                    filled=True, fill_color=ft.Colors.with_opacity(0.06, ft.Colors.TEAL),
                    border=ft.OutlineInputBorder(border_radius=ft.BorderRadius.all(10)),
                ),
                ft.Text("至", size=12, color=ft.Colors.BLUE_GREY),
                ft.Dropdown(
                    label="结束", value=chart_state["end"], options=_month_options(end_candidates),
                    on_select=choose_chart_end, width=month_width, height=48, dense=True, text_size=13,
                    content_padding=ft.Padding.symmetric(horizontal=8, vertical=0),
                    filled=True, fill_color=ft.Colors.with_opacity(0.06, ft.Colors.TEAL),
                    border=ft.OutlineInputBorder(border_radius=ft.BorderRadius.all(10)),
                ),
            ],
        )
        series_filters = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            controls=[
                ft.Checkbox(
                    label=label,
                    value=chart_state[state_key],
                    active_color=color,
                    label_style=ft.TextStyle(size=12),
                    width=76,
                    on_change=lambda e, key=state_key, setting=setting_key: toggle_series(e, key, setting),
                )
                for label, state_key, setting_key, color, _values in series_config
            ],
        )
        trend_controls = [
            ft.Text("月度账单趋势", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("选择连续 2–12 个月，并勾选要显示的曲线。", size=12, color=ft.Colors.BLUE_GREY),
            selectors,
            series_filters,
        ]
        visible_series = [item for item in series_config if chart_state[item[1]]]
        if range_records:
            chart = LineChart(
                data_series=[series(label, color, values) for label, _key, _setting, color, values in visible_series],
                min_x=0,
                max_x=len(chart_months) - 1,
                min_y=min_y,
                max_y=max_y,
                horizontal_grid_lines=ChartGridLines(interval=y_step, color=ft.Colors.with_opacity(0.14, ft.Colors.BLUE_GREY), width=1),
                left_axis=ChartAxis(labels=y_labels, label_size=54),
                bottom_axis=ChartAxis(labels=x_labels, label_size=30),
                interactive=True,
                width=max(240, (page.width or 360) - 64),
                height=245,
            )
            summary_columns = [
                ft.Column([
                    ft.Text(f"期间{label}", size=11, color=ft.Colors.BLUE_GREY),
                    ft.Text(_money(sum(values)), color=color, weight=ft.FontWeight.BOLD),
                ], spacing=2)
                for label, _key, _setting, color, values in visible_series
            ]
            summary = ft.Row(
                summary_columns,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN if len(summary_columns) > 1 else ft.MainAxisAlignment.CENTER,
            )
            trend_controls.extend([chart, ft.Divider(height=1), summary])
        else:
            trend_controls.append(ft.Container(
                height=190,
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=36, color=ft.Colors.BLUE_GREY),
                    ft.Text("所选月份区间暂无账单记录", color=ft.Colors.BLUE_GREY),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            ))
        trend_card = ft.Card(content=ft.Container(content=ft.Column(trend_controls, spacing=10), padding=14))

        root.controls = [
            ft.Text("收支日历", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                ft.TextButton(content="‹ 上月", on_click=lambda: shift_month(-1)),
                ft.Text(month_title, size=18, weight=ft.FontWeight.BOLD),
                ft.TextButton(content="下月 ›", on_click=lambda: shift_month(1)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            trend_card,
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
