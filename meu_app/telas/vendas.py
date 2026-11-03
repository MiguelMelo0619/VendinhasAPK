from datetime import datetime
from functools import partial
from uuid import uuid4

import flet as ft

from formatacao import ler_quantidade, moeda
import ui_comum


def criar_vendas(page, estado, voltar):
    produtos = estado.produtos
    vendas = estado.vendas
    salvar = estado.salvar
    produto_por_id = estado.produto_por_id

    aviso = partial(ui_comum.aviso, page)
    abrir = partial(ui_comum.abrir, page)
    fechar = partial(ui_comum.fechar, page)

    def cabecalho(titulo):
        return ui_comum.cabecalho(titulo, voltar)

    # ----------------------------------------------------------
    # VENDAS: utiliza produtos cadastrados e congela preço e comissão
    # ----------------------------------------------------------
    linhas_venda = ft.Column(spacing=6, scroll="auto")
    campos_qtd = {}
    lista_vendas = ft.Column(spacing=8)
    texto_resumo = ft.Column(spacing=4)
    # Em vez de uma frase longa, valores em cartões que se ajustam à largura.
    texto_total_vendas = ft.Text(weight="bold", size=21, color="#4ade80")
    texto_total_vendedor = ft.Text(weight="bold", size=21, color="#4ade80")
    painel_financeiro = ft.ResponsiveRow([
        ft.Container(
            col={"xs": 12, "sm": 6},
            padding=14, border_radius=12, bgcolor="#193024",
            content=ft.Column([
                ft.Text("Total de vendas", size=13, color="#d1fae5"),
                texto_total_vendas,
            ], spacing=5, tight=True),
        ),
        ft.Container(
            col={"xs": 12, "sm": 6},
            padding=14, border_radius=12, bgcolor="#193024",
            content=ft.Column([
                ft.Text("Total do vendedor", size=13, color="#d1fae5"),
                texto_total_vendedor,
            ], spacing=5, tight=True),
        ),
    ], spacing=10, run_spacing=10)

    def criar_linha_venda(produto):
        pid = produto["id"]
        campo = ft.TextField(
            value="0",
            width=72,
            height=44,
            text_align="center",
            keyboard_type=ft.KeyboardType.NUMBER,
            dense=True,
            content_padding=10,
        )
        campos_qtd[pid] = campo

        def alterar(delta):
            try:
                n = ler_quantidade(campo.value)
            except ValueError:
                n = 0
            campo.value = str(max(0, n + delta))
            campo.update()

        return ft.Container(
            padding=12,
            border_radius=12,
            bgcolor="#2a2f39",
            content=ft.Column([
                ft.Text(produto["nome"], size=15, weight="bold", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(moeda(produto["preco"]), size=13, color="#cbd5e1"),
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=24, on_click=lambda e: alterar(-1)),
                    campo,
                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=24, on_click=lambda e: alterar(1)),
                ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=8, tight=True),
        )

    def abrir_venda(e):
        if not produtos:
            aviso("Cadastre pelo menos um produto antes de registrar vendas.", True)
            return
        campos_qtd.clear()
        linhas_venda.controls = [criar_linha_venda(p) for p in produtos]
        abrir(venda_dialog)

    async def registrar_venda(e):
        try:
            quantidades = {pid: ler_quantidade(campo.value) for pid, campo in campos_qtd.items()}
        except ValueError as exc:
            aviso(str(exc), True)
            return
        itens = []
        for pid, qtd in quantidades.items():
            if qtd:
                p = produto_por_id(pid)
                if p:
                    # Fotografia do produto no momento da venda, em centavos.
                    itens.append({"id": pid, "nome": p["nome"], "quantidade": qtd,
                                  "preco": p["preco"], "vendedor": p["vendedor"]})
        if not itens:
            aviso("Selecione pelo menos uma unidade.", True)
            return
        vendas.append({"id": str(uuid4()), "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "itens": itens})
        await salvar()
        fechar(venda_dialog)
        atualizar_vendas()
        aviso("Venda registrada.")

    venda_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Registrar venda", size=20, weight="bold"),
        content=ft.Container(
            content=linhas_venda,
            width=340,
            height=430,
            padding=ft.Padding(top=6, left=0, right=0, bottom=0),
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(venda_dialog)),
            ft.FilledButton("Confirmar", on_click=registrar_venda),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    def atualizar_vendas():
        totais_qtd = {}
        total_vendas = 0
        total_vendedor = 0
        lista_vendas.controls.clear()
        for venda in vendas:
            for item in venda["itens"]:
                chave = item["id"]
                if chave not in totais_qtd:
                    totais_qtd[chave] = {"nome": item["nome"], "quantidade": 0}
                totais_qtd[chave]["quantidade"] += item["quantidade"]
                total_vendas += item["quantidade"] * item["preco"]
                total_vendedor += item["quantidade"] * item["vendedor"]
        texto_resumo.controls = (
            [ft.Container(
                padding=ft.Padding(top=6, bottom=6, left=10, right=10),
                border_radius=8,
                bgcolor="#20252e",
                content=ft.Row([
                    ft.Text(v["nome"], size=14, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(
                        padding=ft.Padding(top=4, bottom=4, left=10, right=10),
                        border_radius=20,
                        bgcolor="#334155",
                        content=ft.Text(str(v["quantidade"]), size=13, weight="bold"),
                    ),
                ], spacing=10),
            ) for v in totais_qtd.values()]
            if totais_qtd else [ft.Text("Nenhuma venda registrada.", size=14)]
        )
        texto_total_vendas.value = moeda(total_vendas)
        texto_total_vendedor.value = moeda(total_vendedor)
        for venda in reversed(vendas):
            descricao = ", ".join(f"{i['quantidade']}x {i['nome']}" for i in venda["itens"])
            total = sum(i["quantidade"] * i["preco"] for i in venda["itens"])
            lista_vendas.controls.append(
                ft.Container(
                    padding=12, border_radius=10, bgcolor="#20252e",
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color="#4ade80", size=19),
                            ft.Text(descricao, size=14, expand=True, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                        ], vertical_alignment="start", spacing=8),
                        ft.Text(moeda(total), size=16, weight="bold", color="#4ade80"),
                        ft.Text(venda["horario"], size=12, color="#aeb8c8"),
                    ], spacing=6, tight=True),
                )
            )
        page.update()

    async def desfazer_venda(e):
        if not vendas:
            aviso("Não há vendas para desfazer.", True)
            return
        vendas.pop()
        await salvar()
        atualizar_vendas()
        aviso("Última venda desfeita.")

    async def zerar_vendas(e):
        vendas.clear()
        await salvar()
        fechar(reset_dialog)
        atualizar_vendas()
        aviso("Vendas zeradas. Os produtos cadastrados foram mantidos.")

    reset_dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Zerar vendas?"),
        content=ft.Text("Isso apagará o histórico e zerará os totais de vendas e do vendedor. O cadastro de produtos e o caixa serão mantidos."),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(reset_dialog)),
            ft.TextButton("Zerar vendas", on_click=zerar_vendas),
        ],
    )

    def mostrar_vendas(e=None):
        page.controls.clear()
        page.add(
            cabecalho("Vendas"),
            ft.FilledButton("Registrar venda", icon=ft.Icons.ADD_SHOPPING_CART,
                            on_click=abrir_venda, height=50, width=260),
            ft.ResponsiveRow([
                ft.FilledTonalButton("Desfazer última", icon=ft.Icons.UNDO,
                                     on_click=desfazer_venda, col={"xs": 12, "sm": 6}),
                ft.OutlinedButton("Zerar vendas", icon=ft.Icons.DELETE_FOREVER,
                                  on_click=lambda e: abrir(reset_dialog), col={"xs": 12, "sm": 6}),
            ], spacing=10, run_spacing=10),
            ft.Divider(),
            ft.Text("Quantidades vendidas", weight="bold"),
            texto_resumo,
            ft.Divider(),
            ft.Text("Financeiro", weight="bold"),
            painel_financeiro,
            ft.Divider(),
            ft.Text("Histórico de vendas", weight="bold"),
            lista_vendas,
        )
        atualizar_vendas()

    return mostrar_vendas
