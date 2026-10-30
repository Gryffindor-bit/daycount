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
PALETTE_SHADE_PREFIX = {
    "青绿": "TEAL",
    "海蓝": "BLUE",
    "靛蓝": "INDIGO",
    "紫罗兰": "DEEP_PURPLE",
    "玫瑰": "PINK",
    "珊瑚橙": "DEEP_ORANGE",
    "琥珀": "AMBER",
    "森林绿": "GREEN",
}
BACKGROUND_SHADES = [50, 100, 200, 300, 400]
BACKGROUND_LABELS = ["最浅", "浅色", "柔和", "加深", "较深"]

FONT_COLORS = [
    ("炭黑", ft.Colors.BLACK),
    ("深蓝灰", ft.Colors.BLUE_GREY_900),
    ("深靛蓝", ft.Colors.INDIGO_900),
    ("墨绿", ft.Colors.GREEN_900),
    ("深棕", ft.Colors.BROWN_900),
]
FONT_COLOR_MAP = {name: color for name, color in FONT_COLORS}


def background_color(settings):
    palette_name = settings.get("theme_color", "青绿")
    prefix = PALETTE_SHADE_PREFIX.get(palette_name, "TEAL")
    try:
        depth = int(float(settings.get("background_depth", "0")))
    except (TypeError, ValueError):
        depth = 0
    depth = max(0, min(depth, len(BACKGROUND_SHADES) - 1))
    return getattr(ft.Colors, f"{prefix}_{BACKGROUND_SHADES[depth]}")


def build_theme(settings):
    seed = PALETTE_MAP.get(settings.get("theme_color", "青绿"), ft.Colors.TEAL)
    font_color = FONT_COLOR_MAP.get(settings.get("font_color", "深蓝灰"), ft.Colors.BLUE_GREY_900)
    try:
        scale = float(settings.get("text_scale", "1.0"))
    except (TypeError, ValueError):
        scale = 1.0
    density = ft.VisualDensity.COMPACT if settings.get("compact_ui", "0") == "1" else ft.VisualDensity.COMFORTABLE
    text_style = lambda size: ft.TextStyle(size=size * scale, color=font_color)
    background = background_color(settings)
    return ft.Theme(
        color_scheme_seed=seed,
        visual_density=density,
        scaffold_bgcolor=background,
        canvas_color=background,
        text_theme=ft.TextTheme(
            body_large=text_style(16),
            body_medium=text_style(14),
            body_small=text_style(12),
            display_large=text_style(57),
            display_medium=text_style(45),
            display_small=text_style(36),
            headline_large=text_style(32),
            headline_medium=text_style(28),
            headline_small=text_style(24),
            label_large=text_style(14),
            label_medium=text_style(12),
            label_small=text_style(11),
            title_large=text_style(22),
            title_medium=text_style(16),
            title_small=text_style(14),
        ),
    )
