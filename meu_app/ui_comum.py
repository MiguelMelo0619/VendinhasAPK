import flet as ft


def aviso(page, mensagem, erro=False):
    page.show_dialog(ft.SnackBar(content=ft.Text(mensagem), bgcolor="#b91c1c" if erro else "#166534"))


def abrir(page, dialogo):
    page.show_dialog(dialogo)


def fechar(page, dialogo):
    page.pop_dialog()


def cabecalho(titulo, voltar):
    return ft.Row([
        ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar),
        ft.Text(titulo, weight="bold", size=21, expand=True),
    ], spacing=8)
