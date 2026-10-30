import flet as ft


PALETTES = [
    ("青绿", ft.Colors.TEAL),
    ("海蓝", ft.Colors.BLUE),
    ("靛蓝", ft.Colors.INDIGO),
    ("紫罗兰", ft.Colors.DEEP_PURPLE),
    ("玫瑰", ft.Colors.PINK),
    ("珊瑚橙", ft.Colors.DEEP_ORANGE),
    ("琥珀", ft.Colors.AMBER),
    ("森林绿", ft.Colors.GREEN),
]
PALETTE_MAP = {name: color for name, color in PALETTES}


def build_theme(settings):
    seed = PALETTE_MAP.get(settings.get("theme_color", "青绿"), ft.Colors.TEAL)
    try:
        scale = float(settings.get("text_scale", "1.0"))
    except (TypeError, ValueError):
        scale = 1.0
    density = ft.VisualDensity.COMPACT if settings.get("compact_ui", "0") == "1" else ft.VisualDensity.COMFORTABLE
    return ft.Theme(
        color_scheme_seed=seed,
        visual_density=density,
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(size=16 * scale),
            body_medium=ft.TextStyle(size=14 * scale),
            body_small=ft.TextStyle(size=12 * scale),
            label_large=ft.TextStyle(size=14 * scale),
            label_medium=ft.TextStyle(size=12 * scale),
            label_small=ft.TextStyle(size=11 * scale),
            title_medium=ft.TextStyle(size=16 * scale),
        ),
    )
