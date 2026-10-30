import flet as ft


APP_VERSION = "1.0.0"
APP_AUTHOR = "Wen Xin"


def build():
    return ft.Column([
        ft.Text("关于每日账本", size=24, weight=ft.FontWeight.BOLD),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=32, color=ft.Colors.TEAL),
                    ft.Text("每日账本", size=22, weight=ft.FontWeight.BOLD)]),
            ft.Divider(),
            ft.ListTile(leading=ft.Icon(ft.Icons.INFO_OUTLINE), title=ft.Text("版本号"), trailing=ft.Text(APP_VERSION)),
            ft.ListTile(leading=ft.Icon(ft.Icons.PERSON_OUTLINE), title=ft.Text("作者"), trailing=ft.Text(APP_AUTHOR)),
            ft.Text("记录每日收支、三餐与生活开销，查看日历明细、预算和月度统计。"),
        ], spacing=8), padding=18)),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
