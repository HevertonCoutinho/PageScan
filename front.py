import flet as ft
import time
from flet import (
    colors
)
import subprocess

def main(page: ft.Page):
    page.theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=ft.colors.ORANGE,
        primary_container=ft.colors.ORANGE_200
        # ...
    ),
)
    texto = ft.Text(value="Page Scan", color="orange")
    page.add(texto)#atalho para page.controls.append(texto) e page.update())
    
    def btn_click(e):
        if not txt_name.value:
            txt_name.error_text = "Informe um URL válido."
            page.update()
        else:
            backend_command = ["python", "pagescan.py", txt_name.value]
            subprocess.run(backend_command)
            name = txt_name.value
            page.clean()
            page.add(ft.Text(f"Escaneando {name}"))

    txt_name = ft.TextField(label="URL")

    page.add(txt_name, ft.ElevatedButton("Escanear", on_click=btn_click))

ft.app(target=main)

