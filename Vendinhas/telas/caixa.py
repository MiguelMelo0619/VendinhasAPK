from functools import partial

import flet as ft

from constantes import DENOMINACOES
from formatacao import ler_quantidade, moeda
import ui_comum


def criar_caixa(page, estado, voltar):
    caixa = estado.caixa
    salvar = estado.salvar

    aviso = partial(ui_comum.aviso, page)
    abrir = partial(ui_comum.abrir, page)
    fechar = partial(ui_comum.fechar, page)

    def cabecalho(titulo):
        return ui_comum.cabecalho(titulo, voltar)

    # ----------------------------------------------------------
    # CAIXA: mantido independente do registro de vendas
    # ----------------------------------------------------------
    texto_total_caixa = ft.Text(weight="bold", size=21, color="#4ade80")
    grid_caixa = ft.Row(wrap=True, alignment="center")
    campos_caixa = {}
    linhas_caixa = ft.Column(spacing=4, scroll="auto")

    def atualizar_caixa():
        total = sum(d * caixa[str(d)] for d in DENOMINACOES)
        texto_total_caixa.value = moeda(total)
        grid_caixa.controls.clear()
        for d in DENOMINACOES:
            if caixa[str(d)] > 0:
                grid_caixa.controls.append(ft.Container(
                    content=ft.Text(f"{moeda(d)}\n{caixa[str(d)]} un", text_align="center", color="#0f172a"),
                    bgcolor="#e2e8f0", padding=12, border_radius=8, width=100,
                ))
        if not grid_caixa.controls:
            grid_caixa.controls.append(ft.Text("A carteira está vazia."))
        page.update()

    def abrir_movimentacao(e):
        campos_caixa.clear()
        linhas_caixa.controls.clear()
        for d in DENOMINACOES:
            campo = ft.TextField(value="0", width=60, text_align="center", keyboard_type=ft.KeyboardType.NUMBER, dense=True)
            campos_caixa[d] = campo

            def alterar(delta, c=campo):
                try:
                    atual = ler_quantidade(c.value)
                except ValueError:
                    atual = 0
                c.value = str(max(0, atual + delta))
                c.update()

            linhas_caixa.controls.append(ft.Row([
                ft.Text(moeda(d), expand=True),
                ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda e, f=alterar: f(-1)),
                campo,
                ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e, f=alterar: f(1)),
            ]))
        abrir(caixa_dialog)

    async def movimentar_caixa(e, sinal):
        try:
            valores = {d: ler_quantidade(c.value) for d, c in campos_caixa.items()}
        except ValueError as exc:
            aviso(str(exc), True)
            return
        if sinal == -1 and any(valores[d] > caixa[str(d)] for d in DENOMINACOES):
            aviso("Não há cédulas/moedas suficientes para essa retirada.", True)
            return
        for d in DENOMINACOES:
            caixa[str(d)] += sinal * valores[d]
        await salvar()
        fechar(caixa_dialog)
        atualizar_caixa()
        aviso("Caixa atualizado.")

    async def retirar_do_caixa(e):
        await movimentar_caixa(e, -1)

    async def adicionar_ao_caixa(e):
        await movimentar_caixa(e, 1)

    caixa_dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Movimentação do caixa"),
        content=ft.Container(content=linhas_caixa, width=300, height=390),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(caixa_dialog)),
            ft.TextButton("Subtrair", on_click=retirar_do_caixa),
            ft.FilledButton("Adicionar", on_click=adicionar_ao_caixa),
        ],
    )

    def mostrar_caixa(e=None):
        page.controls.clear()
        page.add(
            cabecalho("Caixa"),
            ft.Text("Total em caixa", size=14, weight="bold"),
            texto_total_caixa,
            ft.FilledButton("Movimentação (+ / -)", icon=ft.Icons.SYNC_ALT, on_click=abrir_movimentacao, height=50),
            ft.Divider(),
            ft.Text("Detalhes da carteira", weight="bold"),
            grid_caixa,
        )
        atualizar_caixa()

    return mostrar_caixa
