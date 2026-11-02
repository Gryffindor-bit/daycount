import flet as ft


APP_VERSION = "1.0.1"
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
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.HELP_OUTLINE, color=ft.Colors.TEAL),
                ft.Text("帮助说明", size=18, weight=ft.FontWeight.BOLD),
            ]),
#            ft.Text(
#                "每日账本是一个免费软件，我们不为其提供任何服务，""请务必不要反馈非应用自身引起的问题。",weight=ft.FontWeight.BOLD
#            ),       
             ft.Text(
                spans=[
                     ft.TextSpan("每日账本是一个"),
                     ft.TextSpan("免费软件", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),    
                     ft.TextSpan("并且我们"),                                        
                     ft.TextSpan("不", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                     ft.TextSpan("为其提供任何服务，"),
                     ft.TextSpan("请务必不要反馈非应用自身引起的问题。",style=ft.TextStyle(weight=ft.FontWeight.BOLD)),                     
                ],
#                color=ft.Colors.RED_600
              ),
            ft.Divider(),
            ft.Row([
                ft.Icon(ft.Icons.CODE, color=ft.Colors.TEAL),
                ft.Column([
                    ft.Text("源代码", weight=ft.FontWeight.BOLD),
                    ft.TextButton(
                        content="Daycount For Android · GitHub",
                        url="https://github.com/Gryffindor-bit/daycount",
                        icon=ft.Icons.OPEN_IN_NEW,
                    ),
                ], spacing=0),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=8), padding=18)),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
