import json
from datetime import date
import sqlite3

import flet as ft


def _message(page, title, content):
    page.show_dialog(ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(content),
        actions=[ft.TextButton(content="知道了", on_click=lambda: page.pop_dialog())],
    ))


def build(page: ft.Page, store, on_restored):
    async def export_backup():
        picker = ft.FilePicker()
        backup = store.export_backup()
        data = json.dumps(backup, ensure_ascii=False, indent=2).encode("utf-8")
        filename = f"daily-ledger-backup-{date.today().isoformat()}.json"
        try:
            saved_path = await picker.save_file(
                dialog_title="保存每日账本备份",
                file_name=filename,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json"],
                src_bytes=data,
            )
        except Exception as exc:
            _message(page, "备份失败", f"无法保存备份文件：{exc}")
            return
        if saved_path:
            _message(page, "备份已保存", "请把这个 JSON 文件保存在应用之外，例如手机文件或云盘。重装后可用“导入备份”恢复。")

    async def select_backup():
        picker = ft.FilePicker()
        try:
            files = await picker.pick_files(
                dialog_title="选择每日账本备份",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["json"],
                allow_multiple=False,
                with_data=True,
            )
        except Exception as exc:
            _message(page, "无法读取备份", f"文件选择失败：{exc}")
            return
        if not files:
            return
        selected = files[0]
        if selected.size > 50 * 1024 * 1024:
            _message(page, "备份文件过大", "请选择小于 50 MB 的账本备份文件。")
            return
        try:
            if selected.bytes is None:
                raise ValueError("无法读取文件内容，请重新选择备份文件。")
            backup = json.loads(selected.bytes.decode("utf-8"))
            if not isinstance(backup, dict) or backup.get("format") != "daily-ledger-backup":
                raise ValueError("这不是每日账本的备份文件。")
            count = len(backup.get("transactions", []))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            _message(page, "备份文件无效", str(exc))
            return

        def cancel():
            page.pop_dialog()

        def confirm():
            try:
                store.import_backup(backup)
            except (ValueError, TypeError, KeyError, sqlite3.Error) as exc:
                page.pop_dialog()
                _message(page, "恢复失败", str(exc))
                return
            page.pop_dialog()
            on_restored()
            _message(page, "恢复完成", f"已从备份恢复 {count} 条账目、分类、预算和界面设置。")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("替换当前数据？"),
            content=ft.Text(f"将用“{selected.name}”替换此设备当前的账目、分类、预算和界面设置。建议先导出当前数据备份。"),
            actions=[
                ft.TextButton(content="取消", on_click=cancel),
                ft.Button(content="确认恢复", on_click=confirm),
            ],
        ))

    return ft.Column([
        ft.Text("数据备份与恢复", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("本机数据库会在卸载应用时被系统清除。请在卸载前导出备份，并保存到应用之外；重装后再导入。"),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Icon(ft.Icons.BACKUP, size=36, color=ft.Colors.TEAL),
            ft.Text("导出完整备份", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("包含所有账目、内置和自定义分类、预算以及界面设置。"),
            ft.Button(content="导出备份文件", icon=ft.Icons.FILE_DOWNLOAD, on_click=export_backup),
        ], spacing=12), padding=18)),
        ft.Card(content=ft.Container(content=ft.Column([
            ft.Icon(ft.Icons.RESTORE, size=36, color=ft.Colors.BLUE),
            ft.Text("从备份恢复", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("选择之前导出的 JSON 备份。恢复会替换当前设备上的数据。"),
            ft.OutlinedButton(content="导入备份文件", icon=ft.Icons.FILE_UPLOAD, on_click=select_backup),
        ], spacing=12), padding=18)),
        ft.Text("请妥善保管备份文件。仅保存在应用私有目录中的文件，卸载时仍可能被删除。", size=12),
    ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
