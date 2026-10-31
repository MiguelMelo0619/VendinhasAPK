import flet as ft

from estado import Estado
from telas.caixa import criar_caixa
from telas.menu import criar_menu
from telas.produtos import criar_produtos
from telas.vendas import criar_vendas


async def main(page: ft.Page):
    page.title = "Vendinhas"
    page.scroll = "auto"
    page.padding = ft.Padding(top=20, left=16, right=16, bottom=28)
    page.fonts = {
        "Cursiva": "https://raw.githubusercontent.com/google/fonts/main/ofl/lobstertwo/LobsterTwo-Regular.ttf"
    }

    estado = Estado()
    await estado.carregar_tudo()

    def voltar(e=None):
        menu_principal(e)

    mostrar_produtos = criar_produtos(page, estado, voltar)
    mostrar_vendas = criar_vendas(page, estado, voltar)
    mostrar_caixa = criar_caixa(page, estado, voltar)

    menu_principal = criar_menu(page, mostrar_vendas, mostrar_produtos, mostrar_caixa)

    menu_principal()


if __name__ == "__main__":
    ft.run(main)
