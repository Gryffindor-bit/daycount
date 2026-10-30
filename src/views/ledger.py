from datetime import date

import flet as ft

from data import MEALS, PAYMENT_METHODS


def _money(value):
    return f"¥{value:,.2f}"


def _options(names):
    return [ft.DropdownOption(key=name, text=name) for name in names]


def open_editor(page: ft.Page, store, on_saved, record=None):
    record = record or {}
    kind = record.get("kind", "支出")
    categories = store.list_categories(kind)
    kind_field = ft.Dropdown(label="收支类型", value=kind, options=_options(["支出", "收入"]))
    category_field = ft.Dropdown(
        label="分类", value=record.get("category", categories[0]["name"]),
        options=_options([item["name"] for item in categories]),
    )
    amount_field = ft.TextField(label="金额（元）", value=str(record.get("amount", "")), keyboard_type=ft.KeyboardType.NUMBER)
    date_field = ft.TextField(label="日期（YYYY-MM-DD）", value=record.get("entry_date", date.today().isoformat()))
    meal_field = ft.Dropdown(label="三餐（餐饮可选）", value=record.get("meal", "不区分"), options=_options(MEALS))
    payment_field = ft.Dropdown(label="支付方式", value=record.get("payment", "现金"), options=_options(PAYMENT_METHODS))
    merchant_field = ft.TextField(label="商家 / 对象（可选）", value=record.get("merchant", ""))
    note_field = ft.TextField(label="备注 / 标签（可选）", value=record.get("note", ""), multiline=True, min_lines=1, max_lines=3)
    error_text = ft.Text("", color=ft.Colors.RED)

    def change_kind(e):
        new_kind = kind_field.value or "支出"
        names = [item["name"] for item in store.list_categories(new_kind)]
        category_field.options = _options(names)
        category_field.value = names[0] if names else None
        page.update()

    kind_field.on_select = change_kind

    def save():
        try:
            amount = float((amount_field.value or "").strip())
            entry_date = (date_field.value or "").strip()
            date.fromisoformat(entry_date)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            error_text.value = "请输入大于 0 的金额，并填写有效日期（YYYY-MM-DD）。"
            page.update()
            return
        result = {
            "amount": amount,
            "kind": kind_field.value or "支出",
            "category": category_field.value or "其他支出",
            "entry_date": entry_date,
            "meal": (meal_field.value or "不区分") if (category_field.value == "餐饮" and kind_field.value == "支出") else "",
            "note": (note_field.value or "").strip(),
            "payment": payment_field.value or "",
            "merchant": (merchant_field.value or "").strip(),
        }
        if record.get("id"):
            store.update_transaction(record["id"], result)
        else:
            store.add_transaction(result)
        page.pop_dialog()
        on_saved()

    def delete():
        if record.get("id"):
            store.delete_transaction(record["id"])
            page.pop_dialog()
            on_saved()

    actions = [ft.TextButton(content="取消", on_click=lambda: page.pop_dialog())]
    if record.get("id"):
        actions.append(ft.TextButton(content="删除", on_click=delete))
    actions.append(ft.Button(content="保存", on_click=save))
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("编辑账目" if record.get("id") else "记一笔"),
        content=ft.Column([
            ft.Row([kind_field, category_field]),
            amount_field,
            date_field,
            meal_field,
            payment_field,
            merchant_field,
            note_field,
            error_text,
        ], tight=True, scroll=ft.ScrollMode.AUTO),
        actions=actions,
        scrollable=True,
    )
    page.show_dialog(dialog)


def build(page: ft.Page, store, on_saved):
    kind_filter = ft.Dropdown(label="筛选", value="全部", options=_options(["全部", "支出", "收入"]))
    content = ft.Column(spacing=6, expand=True, scroll=ft.ScrollMode.AUTO)

    def refresh(update_page=False):
        kind = None if kind_filter.value == "全部" else kind_filter.value
        records = store.transactions(kind=kind)
        content.controls = [ft.Text(f"共 {len(records)} 笔记录", color=ft.Colors.BLUE_GREY)]
        if not records:
            content.controls.append(ft.Text("暂无记录。可通过右下角 + 添加收入、支出和三餐明细。"))
        icons = {c["name"]: c["icon"] for c in store.list_categories()}
        for item in records:
            subtitle = " · ".join(part for part in [item["entry_date"], item.get("meal"), item.get("merchant"), item.get("note"), item.get("payment")] if part)
            content.controls.append(ft.ListTile(
                leading=ft.Icon(getattr(ft.Icons, icons.get(item["category"], "CATEGORY"), ft.Icons.CATEGORY)),
                title=ft.Text(item["category"]),
                subtitle=ft.Text(subtitle),
                trailing=ft.Text(("+" if item["kind"] == "收入" else "−") + _money(item["amount"]),
                                 color=ft.Colors.GREEN if item["kind"] == "收入" else ft.Colors.RED),
                on_click=lambda e, rid=item["id"]: open_editor(page, store, lambda: refresh(True), store.get_transaction(rid)), 
            ))
        if update_page:
            page.update()

    kind_filter.on_select = lambda e: refresh(True)
    refresh()
    return ft.Column([
        ft.Text("收支明细", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("点开任一记录即可修改或删除。支持商家、支付方式、备注和餐次。"),
        kind_filter,
        content,
    ], spacing=10, expand=True)
