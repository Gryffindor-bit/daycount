import logging
from pathlib import Path

import flet as ft

from storage import LedgerStore
from theme import build_theme
from views import about, appearance, calendar as calendar_view, home, ledger, reports

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")

PAGE_KEYS = ["home", "ledger", "calendar", "reports", "appearance", "about"]
PAGE_TITLES = ["首页", "收支明细", "收支日历", "月度统计", "界面设置", "关于每日账本"]


async def main(page: ft.Page):
    page.title = "每日账本"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.GREY_50
    page.padding = 0

    if page.web:
        database_path = ":memory:"
        preview_only = True
    else:
        paths = ft.StoragePaths()
        database_path = str(Path(await paths.get_application_documents_directory()) / "daily_ledger.sqlite3")
        preview_only = False

    store = LedgerStore(database_path)
    log.info("ledger database ready (temporary preview=%s)", preview_only)
    active = {"key": "home"}
    bottom_keys = PAGE_KEYS[:4]

    navigation = ft.NavigationBar(
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="首页"),
            ft.NavigationBarDestination(icon=ft.Icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.Icons.RECEIPT_LONG, label="明细"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, selected_icon=ft.Icons.CALENDAR_MONTH, label="日历"),
            ft.NavigationBarDestination(icon=ft.Icons.PIE_CHART_OUTLINE, selected_icon=ft.Icons.PIE_CHART, label="统计"),
        ],
    )
    drawer = ft.NavigationDrawer(
        selected_index=0,
        controls=[
            ft.NavigationDrawerDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="首页"),
            ft.NavigationDrawerDestination(icon=ft.Icons.RECEIPT_LONG_OUTLINED, selected_icon=ft.Icons.RECEIPT_LONG, label="收支明细"),
            ft.NavigationDrawerDestination(icon=ft.Icons.CALENDAR_MONTH, selected_icon=ft.Icons.CALENDAR_MONTH, label="收支日历"),
            ft.NavigationDrawerDestination(icon=ft.Icons.PIE_CHART_OUTLINE, selected_icon=ft.Icons.PIE_CHART, label="月度统计"),
            ft.NavigationDrawerDestination(icon=ft.Icons.PALETTE, selected_icon=ft.Icons.PALETTE, label="界面设置"),
            ft.NavigationDrawerDestination(icon=ft.Icons.INFO_OUTLINE, selected_icon=ft.Icons.INFO, label="关于 / 版本 / 作者"),
        ],
    )

    def render():
        page.clean()
        settings = {
            "theme_color": store.get_setting("theme_color", "青绿"),
            "compact_ui": store.get_setting("compact_ui", "0"),
            "text_scale": store.get_setting("text_scale", "1.0"),
        }
        page.theme = build_theme(settings)
        key = active["key"]
        drawer.selected_index = PAGE_KEYS.index(key)
        navigation.selected_index = bottom_keys.index(key) if key in bottom_keys else 0
        page.appbar = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.MENU, tooltip="打开侧边栏", on_click=open_drawer),
            leading_width=48,
            title=ft.Text(PAGE_TITLES[PAGE_KEYS.index(key)], weight=ft.FontWeight.BOLD),
            actions=[ft.IconButton(icon=ft.Icons.ADD, tooltip="记一笔", on_click=add_record)] if key in bottom_keys else [],
        )
        page.navigation_bar = navigation if key in bottom_keys else None
        page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, tooltip="记一笔", on_click=add_record) if key in bottom_keys else None

        if key == "home":
            view = home.build(page, store)
        elif key == "ledger":
            view = ledger.build(page, store, render)
        elif key == "calendar":
            view = calendar_view.build(page, store)
        elif key == "reports":
            view = reports.build(page, store, render)
        elif key == "appearance":
            view = appearance.build(page, store, render)
        else:
            view = about.build()

        content = [view]
        if preview_only:
            content.append(ft.Text("预览环境为临时数据库；安装到手机后账目保存在本机。", size=12, color=ft.Colors.BLUE_GREY))
        page.add(ft.SafeArea(
            content=ft.Container(content=ft.Column(content, expand=True), padding=16, expand=True),
            expand=True,
        ))
        page.update()

    async def open_drawer():
        await page.show_drawer()

    async def on_drawer_change(e):
        active["key"] = PAGE_KEYS[e.control.selected_index]
        await page.close_drawer()
        render()

    def on_navigation(e):
        active["key"] = bottom_keys[e.control.selected_index]
        render()

    def add_record():
        ledger.open_editor(page, store, render)

    navigation.on_change = on_navigation
    drawer.on_change = on_drawer_change
    page.drawer = drawer
    render()


ft.run(main)
