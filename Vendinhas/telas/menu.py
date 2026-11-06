import flet as ft

import ui_comum


def criar_menu(page, mostrar_vendas, mostrar_produtos, mostrar_caixa):
    def menu_principal(e=None):
        ui_comum.mostrar(
            page,
            ft.Text("Vendinhas", size=40, weight="bold", font_family="Cursiva", text_align="center"),
            ft.Divider(height=25, color="transparent"),
            ui_comum.botao("Vendas", ft.Icons.POINT_OF_SALE, mostrar_vendas),
            ui_comum.botao("Produtos", ft.Icons.INVENTORY_2_OUTLINED, mostrar_produtos),
            ui_comum.botao("Caixa", ft.Icons.ACCOUNT_BALANCE_WALLET, mostrar_caixa),
        )

    return menu_principal
