import flet as ft

from theme import PALETTES


def build(page: ft.Page, store, on_changed):
    selected = store.get_setting("theme_color", "青绿")
    palette_buttons = []
    for name, color in PALETTES:
        is_selected = name == selected
        palette_buttons.append(ft.OutlinedButton(
            content=ft.Row([
                ft.Container(width=18, height=18, bgcolor=color, border_radius=9),
                ft.Text(name),
                *([ft.Icon(ft.Icons.CHECK, size=16)] if is_selected else []),
            ], spacing=8, tight=True),
            on_click=lambda e, key=name: choose_palette(key),
        ))

    def choose_palette(name):
        store.set_setting("theme_color", name)
        on_changed()

    scale = float(store.get_setting("text_scale", "1.0"))
    scale_label = ft.Text(f"字号：{scale:.0%}")
    slider = ft.Slider(value=scale, min=0.8, max=1.3, divisions=10, label="{value}")

    def preview_scale(e):
        scale_label.value = f"字号：{float(e.control.value):.0%}"
        page.update()

    def save_scale(e):
        store.set_setting("text_scale", str(round(float(e.control.value), 2)))
        on_changed()

    slider.on_change = preview_scale
    slider.on_change_end = save_scale

    compact = ft.Switch(
        label="紧凑布局",
        value=store.get_setting("compact_ui", "0") == "1",
        on_change=lambda e: save_density(e.control.value),
    )

    def save_density(enabled):
        store.set_setting("compact_ui", "1" if enabled else "0")
        on_changed()

    return ft.Column([
        ft.Text("界面设置", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("调整主题色、字号与控件密度，设置会保存在本机。"),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.PALETTE), ft.Text("主题颜色", size=18, weight=ft.FontWeight.BOLD)]),
            ft.Text("选择喜欢的主色，导航栏、按钮和重点控件会同步变化。"),
            ft.Row(palette_buttons, wrap=True, spacing=8, run_spacing=8),
        ], spacing=12), padding=16)),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.TEXT_INCREASE), ft.Text("文字大小", size=18, weight=ft.FontWeight.BOLD)]),
            scale_label,
            slider,
        ], spacing=10), padding=16)),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.DENSITY_SMALL), ft.Text("布局密度", size=18, weight=ft.FontWeight.BOLD)]),
            compact,
            ft.Text("紧凑模式会减少控件的默认留白；关闭后使用舒适布局。"),
        ], spacing=8), padding=16)),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
