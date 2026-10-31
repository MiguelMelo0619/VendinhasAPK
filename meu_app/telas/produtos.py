from functools import partial
from uuid import uuid4

import flet as ft

from formatacao import ler_preco, moeda
import ui_comum


def criar_produtos(page, estado, voltar):
    produtos = estado.produtos
    salvar = estado.salvar
    produto_por_id = estado.produto_por_id

    aviso = partial(ui_comum.aviso, page)
    abrir = partial(ui_comum.abrir, page)
    fechar = partial(ui_comum.fechar, page)

    def cabecalho(titulo):
        return ui_comum.cabecalho(titulo, voltar)

    # ----------------------------------------------------------
    # CADASTRO DE PRODUTOS: adicionar, editar e excluir
    # ----------------------------------------------------------
    campo_nome = ft.TextField(label="Nome do produto", autofocus=True)
    campo_preco = ft.TextField(label="Preço de venda (R$)", hint_text="Ex.: 5,00", keyboard_type=ft.KeyboardType.TEXT)
    campo_vendedor = ft.TextField(label="Valor do vendedor por unidade (R$)", hint_text="Ex.: 1,10", keyboard_type=ft.KeyboardType.TEXT)
    catalogo_lista = ft.Column(spacing=8)
    editando_id = None

    def atualizar_catalogo():
        catalogo_lista.controls.clear()
        if not produtos:
            catalogo_lista.controls.append(ft.Text("Nenhum produto cadastrado. Toque em 'Novo produto' para começar."))
        for produto in produtos:
            pid = produto["id"]
            catalogo_lista.controls.append(
                ft.Container(
                    padding=10,
                    border_radius=8,
                    bgcolor="#f1f5f9",
                    content=ft.Row(
                        controls=[
                            ft.Column([
                                ft.Text(produto["nome"], weight="bold", color="#0f172a"),
                                ft.Text(
                                    f"Venda: {moeda(produto['preco'])}  |  Vendedor: {moeda(produto['vendedor'])}",
                                    size=12, color="#334155",
                                ),
                            ], expand=True, spacing=3),
                            ft.IconButton(ft.Icons.EDIT, tooltip="Editar produto", on_click=lambda e, x=pid: abrir_editor(x)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Excluir produto", on_click=lambda e, x=pid: confirmar_exclusao(x)),
                        ]
                    ),
                )
            )
        page.update()

    def abrir_editor(pid=None):
        nonlocal editando_id
        editando_id = pid
        p = produto_por_id(pid) if pid else None
        editor_dialog.title.value = "Editar produto" if p else "Novo produto"
        campo_nome.value = p["nome"] if p else ""
        campo_preco.value = f"{p['preco'] / 100:.2f}".replace(".", ",") if p else ""
        campo_vendedor.value = f"{p['vendedor'] / 100:.2f}".replace(".", ",") if p else ""
        abrir(editor_dialog)

    async def salvar_produto(e):
        nome = (campo_nome.value or "").strip()
        if not nome:
            aviso("Informe o nome do produto.", True)
            return
        try:
            preco = ler_preco(campo_preco.value)
            vendedor = ler_preco(campo_vendedor.value)
        except ValueError as exc:
            aviso(str(exc), True)
            return
        if vendedor > preco:
            aviso("O valor do vendedor não pode superar o preço de venda.", True)
            return
        if any(p["nome"].casefold() == nome.casefold() and p["id"] != editando_id for p in produtos):
            aviso("Já existe um produto com esse nome.", True)
            return
        if editando_id:
            p = produto_por_id(editando_id)
            if not p:
                aviso("Produto não encontrado.", True)
                return
            p.update(nome=nome, preco=preco, vendedor=vendedor)
        else:
            produtos.append({"id": str(uuid4()), "nome": nome, "preco": preco, "vendedor": vendedor})
        await salvar()
        fechar(editor_dialog)
        atualizar_catalogo()
        aviso("Produto salvo com sucesso.")

    editor_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Novo produto"),
        content=ft.Container(width=300, content=ft.Column(
            [campo_nome, campo_preco, campo_vendedor], tight=True, spacing=12
        )),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(editor_dialog)),
            ft.FilledButton("Salvar", on_click=salvar_produto),
        ],
    )

    excluir_id = None

    def confirmar_exclusao(pid):
        nonlocal excluir_id
        excluir_id = pid
        p = produto_por_id(pid)
        excluir_dialog.content.value = f"Excluir '{p['nome']}' do cadastro? As vendas já realizadas serão preservadas."
        abrir(excluir_dialog)

    async def excluir_produto(e):
        produtos[:] = [p for p in produtos if p["id"] != excluir_id]
        await salvar()
        fechar(excluir_dialog)
        atualizar_catalogo()
        aviso("Produto excluído do cadastro.")

    excluir_dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Excluir produto"),
        content=ft.Text(""),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar(excluir_dialog)),
            ft.TextButton("Excluir", on_click=excluir_produto),
        ],
    )

    def mostrar_produtos(e=None):
        page.controls.clear()
        page.add(
            cabecalho("Produtos"),
            ft.FilledButton("Novo produto", icon=ft.Icons.ADD, on_click=lambda e: abrir_editor()),
            ft.Divider(),
            catalogo_lista,
        )
        atualizar_catalogo()

    return mostrar_produtos
