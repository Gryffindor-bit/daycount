import asyncio
import logging
from pathlib import Path

import flet as ft

from storage import LedgerStore
from theme import background_color, build_theme
from views import about, appearance, backup, calendar as calendar_view, home, ledger, reports

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")

PAGE_KEYS = ["home", "ledger", "calendar", "reports", "appearance", "backup", "about"]
PAGE_TITLES = ["首页", "收支明细", "收支日历", "月度统计", "界面设置", "数据备份", "关于每日账本"]


async def main(page: ft.Page):
    page.title = "每日账本"
    page.theme_mode = ft.ThemeMode.LIGHT
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
    close_state = {"dialog_open": False}
    bottom_keys = PAGE_KEYS[:4]
    fab_position = {
        "right": 16.0,
        "bottom": 16.0,
        "width": 0.0,
        "height": 0.0,
    }
    try:
        fab_position["right"] = max(8.0, float(store.get_setting("fab_right", "16")))
        fab_position["bottom"] = max(8.0, float(store.get_setting("fab_bottom", "16")))
    except (TypeError, ValueError):
        pass

    def cat_nav_image(asset_name):
        return ft.Image(
            src=asset_name,
            width=30,
            height=30,
            fit=ft.BoxFit.CONTAIN,
            exclude_from_semantics=True,
        )

    navigation = ft.NavigationBar(
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=cat_nav_image("cat_home.svg"), selected_icon=cat_nav_image("cat_home.svg"), label="首页"),
            ft.NavigationBarDestination(icon=cat_nav_image("cat_ledger.svg"), selected_icon=cat_nav_image("cat_ledger.svg"), label="明细"),
            ft.NavigationBarDestination(icon=cat_nav_image("cat_calendar.svg"), selected_icon=cat_nav_image("cat_calendar.svg"), label="日历"),
            ft.NavigationBarDestination(icon=cat_nav_image("cat_stats.svg"), selected_icon=cat_nav_image("cat_stats.svg"), label="统计"),
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
            ft.NavigationDrawerDestination(icon=ft.Icons.BACKUP, selected_icon=ft.Icons.BACKUP, label="数据备份与恢复"),
            ft.NavigationDrawerDestination(icon=ft.Icons.INFO_OUTLINE, selected_icon=ft.Icons.INFO, label="关于 / 版本 / 作者"),
        ],
    )
    particle_specs = [
        (278, 86, 9, ft.Colors.CYAN_300, True),
        (293, 142, 6, ft.Colors.AMBER_300, False),
        (270, 198, 12, ft.Colors.PINK_200, True),
        (290, 260, 7, ft.Colors.LIGHT_GREEN_300, False),
        (276, 324, 10, ft.Colors.AMBER_200, True),
        (294, 392, 6, ft.Colors.CYAN_200, False),
        (267, 458, 11, ft.Colors.PURPLE_200, True),
        (287, 526, 7, ft.Colors.PINK_200, False),
        (273, 594, 10, ft.Colors.LIGHT_GREEN_300, True),
        (294, 658, 6, ft.Colors.AMBER_300, False),
    ]
    particle_state = {"stack": None, "particles": [], "generation": 0}

    async def animate_drawer_particles(opening):
        particle_state["generation"] += 1
        generation = particle_state["generation"]
        stack = particle_state["stack"]

        if opening:
            if stack is None:
                particles = []
                for x, y, size, color, is_sparkle in particle_specs:
                    core = (
                        ft.Icon(ft.Icons.AUTO_AWESOME, size=size, color=color)
                        if is_sparkle
                        else None
                    )
                    particle = ft.Container(
                        left=x - 20,
                        top=y,
                        width=size + (8 if is_sparkle else 0),
                        height=size + (8 if is_sparkle else 0),
                        alignment=ft.Alignment.CENTER,
                        bgcolor=None if is_sparkle else color,
                        border_radius=ft.BorderRadius.all(20),
                        shadow=ft.BoxShadow(
                            color=ft.Colors.with_opacity(0.48, color),
                            blur_radius=15,
                            spread_radius=2,
                        ),
                        content=core,
                        ignore_interactions=True,
                        opacity=0,
                        scale=0.45,
                        animate_opacity=ft.Animation(duration=420, curve=ft.AnimationCurve.EASE_OUT_CUBIC),
                        animate_scale=ft.Animation(duration=480, curve=ft.AnimationCurve.EASE_OUT_CUBIC),
                        animate_position=ft.Animation(duration=500, curve=ft.AnimationCurve.EASE_OUT_CUBIC),
                    )
                    particles.append(particle)
                stack = ft.Stack(expand=True, controls=particles, clip_behavior=ft.ClipBehavior.NONE)
                particle_state["stack"] = stack
                particle_state["particles"] = particles
                page.overlay.append(stack)
            particles = particle_state["particles"]
            for particle, (x, y, _size, _color, _sparkle) in zip(particles, particle_specs):
                particle.left = x - 20
                particle.top = y
                particle.opacity = 0
                particle.scale = 0.45
            page.update()
            for particle, (x, y, _size, _color, _sparkle) in zip(particles, particle_specs):
                if generation != particle_state["generation"]:
                    return
                particle.left = x
                particle.top = y
                particle.opacity = 1
                particle.scale = 1
                page.update()
                await asyncio.sleep(0.035)
            return

        if stack is None:
            return
        particles = particle_state["particles"]
        for index, (particle, (x, y, _size, _color, _sparkle)) in enumerate(zip(particles, particle_specs)):
            particle.left = x + 24
            particle.top = y + (-8 if index % 2 else 8)
            particle.opacity = 0
            particle.scale = 0.25
            page.update()
            await asyncio.sleep(0.025)
        await asyncio.sleep(0.48)
        if generation == particle_state["generation"] and stack in page.overlay:
            page.overlay.remove(stack)
            particle_state["stack"] = None
            particle_state["particles"] = []
            page.update()

    def on_drawer_dismiss(_event):
        asyncio.create_task(animate_drawer_particles(False))

    drawer.on_dismiss = on_drawer_dismiss
    fab_widget = {"container": None}

    def clamp_fab_position():
        if fab_position["width"] > 0:
            fab_position["right"] = min(fab_position["right"], max(8.0, fab_position["width"] - 64.0))
        if fab_position["height"] > 0:
            fab_position["bottom"] = min(fab_position["bottom"], max(8.0, fab_position["height"] - 64.0))

    def on_stack_size_change(e):
        fab_position["width"] = e.width
        fab_position["height"] = e.height
        clamp_fab_position()
        container = fab_widget["container"]
        if container is not None:
            container.right = fab_position["right"]
            container.bottom = fab_position["bottom"]
            page.update()

    def on_fab_pan_update(e):
        delta = e.global_delta
        if delta is None:
            return
        fab_position["right"] -= delta.x
        fab_position["bottom"] -= delta.y
        clamp_fab_position()
        container = fab_widget["container"]
        if container is not None:
            container.right = fab_position["right"]
            container.bottom = fab_position["bottom"]
            page.update()

    def on_fab_pan_end(_e):
        store.set_setting("fab_right", str(fab_position["right"]))
        store.set_setting("fab_bottom", str(fab_position["bottom"]))

    def render():
        page.clean()
        settings = {
            "theme_color": store.get_setting("theme_color", "青绿"),
            "compact_ui": store.get_setting("compact_ui", "0"),
            "text_scale": store.get_setting("text_scale", "1.0"),
            "font_color": store.get_setting("font_color", "深蓝灰"),
            "background_depth": store.get_setting("background_depth", "0"),
        }
        page.theme = build_theme(settings)
        page.bgcolor = background_color(settings)
        key = active["key"]
        page.drawer = drawer
        drawer.selected_index = PAGE_KEYS.index(key)
        navigation.selected_index = bottom_keys.index(key) if key in bottom_keys else 0
        page.appbar = ft.AppBar(
            leading=ft.IconButton(icon=ft.Icons.MENU, tooltip="打开侧边栏", on_click=open_drawer),
            leading_width=48,
            title=ft.Text(PAGE_TITLES[PAGE_KEYS.index(key)], weight=ft.FontWeight.BOLD),
            actions=[ft.IconButton(icon=ft.Icons.ADD, tooltip="记一笔", on_click=add_record)] if key in bottom_keys else [],
        )
        page.navigation_bar = navigation if key in bottom_keys else None
        page.floating_action_button = None

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
        elif key == "backup":
            view = backup.build(page, store, render)
        else:
            view = about.build()

        content = [view]
        if preview_only:
            content.append(ft.Text("预览环境为临时数据库；安装到手机后账目保存在本机。", size=12, color=ft.Colors.BLUE_GREY))
        stack_controls = [ft.Container(content=ft.Column(content, expand=True), padding=16, expand=True)]
        fab_widget["container"] = None
        if key in bottom_keys:
            clamp_fab_position()
            floating_button = ft.Container(
                right=fab_position["right"],
                bottom=fab_position["bottom"],
                width=56,
                height=56,
                content=ft.GestureDetector(
                    content=ft.FloatingActionButton(
                        icon=ft.Icons.ADD,
                        tooltip="记一笔（可拖动调整位置）",
                        on_click=add_record,
                    ),
                    on_pan_update=on_fab_pan_update,
                    on_pan_end=on_fab_pan_end,
                ),
            )
            fab_widget["container"] = floating_button
            stack_controls.append(floating_button)
        page.add(ft.SafeArea(
            content=ft.Stack(
                expand=True,
                on_size_change=on_stack_size_change,
                controls=stack_controls,
            ),
            expand=True,
        ))
        page.update()

    async def open_drawer():
        asyncio.create_task(animate_drawer_particles(True))
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

    def request_close():
        if close_state["dialog_open"]:
            return
        close_state["dialog_open"] = True

        def keep_using():
            close_state["dialog_open"] = False
            page.pop_dialog()

        async def confirm_close():
            close_state["dialog_open"] = False
            page.pop_dialog()
            if not page.web:
                page.window.prevent_close = False
                await page.window.close()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("确认退出"),
            content=ft.Text("确定要关闭每日账本吗？未导出的数据仍保存在本机。"),
            actions=[
                ft.TextButton(content="继续使用", on_click=keep_using),
                ft.Button(content="退出应用", on_click=confirm_close),
            ],
        ))

    def on_window_event(e):
        if e.type == ft.WindowEventType.CLOSE:
            request_close()

    def on_keyboard_event(e):
        if not page.web and str(e.key).lower() in {"escape", "back", "browserback"}:
            request_close()

    async def show_startup_animation():
        settings = {
            "theme_color": store.get_setting("theme_color", "青绿"),
            "compact_ui": store.get_setting("compact_ui", "0"),
            "text_scale": store.get_setting("text_scale", "1.0"),
            "font_color": store.get_setting("font_color", "深蓝灰"),
            "background_depth": store.get_setting("background_depth", "0"),
        }
        page.theme = build_theme(settings)
        page.bgcolor = background_color(settings)
        splash = ft.Container(
            content=ft.Column([
                ft.Image(src="icon.png", width=104, height=104, fit=ft.BoxFit.CONTAIN),
                ft.Text("每日账本", size=26, weight=ft.FontWeight.BOLD),
                ft.Text("认真记录，好好生活。"),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.Alignment.CENTER,
            expand=True,
            opacity=0,
            scale=0.86,
            animate_opacity=ft.Animation(duration=720, curve=ft.AnimationCurve.EASE_OUT_CUBIC),
            animate_scale=ft.Animation(duration=720, curve=ft.AnimationCurve.EASE_OUT_CUBIC),
        )
        page.add(splash)
        page.update()
        splash.opacity = 1
        splash.scale = 1
        page.update()
        await asyncio.sleep(1.05)
        page.clean()

    navigation.on_change = on_navigation
    drawer.on_change = on_drawer_change
    page.drawer = drawer
    page.on_keyboard_event = on_keyboard_event
    if not page.web:
        page.window.prevent_close = True
        page.window.on_event = on_window_event

    await show_startup_animation()
    render()


ft.run(main)
