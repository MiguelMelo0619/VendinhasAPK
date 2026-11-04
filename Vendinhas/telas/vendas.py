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
    editando_venda_id = None
    excluindo_venda_id = None
    produtos_para_adicionar = []
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

    def localizar_venda(vid):
        return next((v for v in vendas if v["id"] == vid), None)

    def criar_linha_venda(produto, quantidade=0):
        pid = produto["id"]
        campo = ft.TextField(
            value=str(quantidade),
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

    def exibir_outros_produtos(e=None):
        """Exibe os itens que ainda não faziam parte da venda em edição."""
        if not produtos_para_adicionar:
            return
        # Preserve os campos e as quantidades já informadas na tela.
        linhas_venda.controls = [
            controle for controle in linhas_venda.controls
            if controle is not botao_adicionar_produtos
        ]
        linhas_venda.controls.append(
            ft.Text("Outros produtos do catálogo", weight="bold", size=15)
        )
        for produto in produtos_para_adicionar:
            linhas_venda.controls.append(criar_linha_venda(produto))
        produtos_para_adicionar.clear()
        page.update()

    botao_adicionar_produtos = ft.OutlinedButton(
        "Adicionar outros produtos",
        icon=ft.Icons.ADD,
        on_click=exibir_outros_produtos,
    )

    def abrir_venda(e=None, venda_id=None):
        nonlocal editando_venda_id
        venda = localizar_venda(venda_id) if venda_id else None
        if venda_id and venda is None:
            aviso("Esta venda não foi encontrada.", True)
            return
        if not produtos and not venda:
            aviso("Cadastre pelo menos um produto antes de registrar vendas.", True)
            return

        editando_venda_id = venda_id
        venda_dialog.title.value = "Editar venda" if venda else "Registrar venda"
        botao_confirmar.text = "Salvar alterações" if venda else "Confirmar"
        campos_qtd.clear()
        produtos_para_adicionar.clear()

        if venda:
            # Os itens da venda conservam seus preços/comissões originais,
            # mesmo após edições ou exclusões no cadastro de produtos.
            linhas_venda.controls = [
                ft.Text("Produtos desta venda", weight="bold", size=15)
            ]
            linhas_venda.controls.extend(
                criar_linha_venda(item, item["quantidade"])
                for item in venda["itens"]
            )
            ids_anteriores = {item["id"] for item in venda["itens"]}
            produtos_para_adicionar.extend(
                produto for produto in produtos
                if produto["id"] not in ids_anteriores
            )
            if produtos_para_adicionar:
                linhas_venda.controls.append(botao_adicionar_produtos)
        else:
            # Em um novo registro, todos os produtos ficam disponíveis.
            linhas_venda.controls = [criar_linha_venda(p) for p in produtos]

        abrir(venda_dialog)

    async def registrar_venda(e):
        try:
            quantidades = {pid: ler_quantidade(campo.value) for pid, campo in campos_qtd.items()}
        except ValueError as exc:
            aviso(str(exc), True)
            return

        venda = localizar_venda(editando_venda_id) if editando_venda_id else None
        if editando_venda_id and venda is None:
            aviso("Esta venda não foi encontrada.", True)
            return
        anteriores = {i["id"]: i for i in venda["itens"]} if venda else {}
        itens = []
        for pid, qtd in quantidades.items():
            if qtd:
                # Preservar o valor da época para itens que já pertenciam à venda.
                p = anteriores.get(pid) or produto_por_id(pid)
                if p:
                    itens.append({"id": pid, "nome": p["nome"], "quantidade": qtd,
                                  "preco": p["preco"], "vendedor": p["vendedor"]})
        if not itens:
            aviso("Selecione pelo menos uma unidade. Para apagar a venda, use Excluir.", True)
            return

        if venda:
            venda["itens"] = itens
        else:
            vendas.append({"id": str(uuid4()), "horario": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "itens": itens})
        await salvar()
        fechar(venda_dialog)
        atualizar_vendas()
        aviso("Venda atualizada." if venda else "Venda registrada.")

    def confirmar_exclusao(venda_id):
        nonlocal excluindo_venda_id
        venda = localizar_venda(venda_id)
        if venda is None:
            aviso("Esta venda não foi encontrada.", True)
            return
        excluindo_venda_id = venda_id
        excluir_dialog.content.value = f"Excluir somente a venda de {venda['horario']}? Esta ação não pode ser desfeita."
        abrir(excluir_dialog)

    async def excluir_venda(e):
        nonlocal excluindo_venda_id
        venda = localizar_venda(excluindo_venda_id)
        if venda is None:
            fechar(excluir_dialog)
            aviso("Esta venda não foi encontrada.", True)
            return
        vendas.remove(venda)
        await salvar()
        fechar(excluir_dialog)
        excluindo_venda_id = None
        atualizar_vendas()
        aviso("Venda excluída.")

    excluir_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Excluir venda?"),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(excluir_dialog)),
            ft.TextButton("Excluir", on_click=excluir_venda),
        ],
    )

    botao_confirmar = ft.FilledButton("Confirmar", on_click=registrar_venda)

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
            botao_confirmar,
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
            venda_id = venda["id"]
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
                        ft.Row([
                            ft.TextButton("Editar", icon=ft.Icons.EDIT,
                                          on_click=lambda e, vid=venda_id: abrir_venda(venda_id=vid)),
                            ft.TextButton("Excluir", icon=ft.Icons.DELETE_OUTLINE,
                                          on_click=lambda e, vid=venda_id: confirmar_exclusao(vid)),
                        ], wrap=True, spacing=8),
                    ], spacing=6, tight=True),
                )
            )
        page.update()

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
            ft.OutlinedButton("Zerar vendas", icon=ft.Icons.DELETE_FOREVER,
                              on_click=lambda e: abrir(reset_dialog)),
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
