import flet as ft


def criar_menu(page, mostrar_vendas, mostrar_produtos, mostrar_caixa):
    def menu_principal(e=None):
        page.controls.clear()
        page.add(ft.Column([
            ft.Text("Vendinhas", size=40, weight="bold", font_family="Cursiva"),
            ft.Divider(height=25, color="transparent"),
            ft.FilledButton("Vendas", icon=ft.Icons.POINT_OF_SALE, on_click=mostrar_vendas, height=52),
            ft.FilledButton("Produtos", icon=ft.Icons.INVENTORY_2_OUTLINED, on_click=mostrar_produtos, height=52),
            ft.FilledButton("Caixa", icon=ft.Icons.ACCOUNT_BALANCE_WALLET, on_click=mostrar_caixa, height=52),
        ], horizontal_alignment="center", spacing=14))
        page.update()

    return menu_principal
