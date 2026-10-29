"""Vendinhas: cadastro livre de produtos, vendas e controle de caixa.

Instale: pip install flet
Execute: python main_editado.py

Os dados desta versão usam chaves próprias (v2) nas preferências locais.
Assim, o primeiro uso começa sem produtos, vendas ou dinheiro em caixa,
sem apagar os dados da versão anterior.
"""

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

import flet as ft


CHAVE_PRODUTOS = "vendinhas_v2_produtos"
CHAVE_VENDAS = "vendinhas_v2_vendas"
CHAVE_CAIXA = "vendinhas_v2_caixa"
DENOMINACOES = [10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5]


def moeda(centavos):
    valor = f"{centavos / 100:,.2f}"
    return "R$ " + valor.replace(",", "X").replace(".", ",").replace("X", ".")


def ler_preco(texto):
    """Aceita 5,50; 5.50; 1.234,56 e valores com R$; retorna centavos."""
    s = str(texto or "").strip().replace("R$", "").replace(" ", "")
    if not s:
        raise ValueError("Informe os dois valores em reais.")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        n = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError("Informe um valor válido, como 5,50.") from exc
    if not n.is_finite() or n < 0:
        raise ValueError("Os valores precisam ser maiores ou iguais a zero.")
    if n.as_tuple().exponent < -2:
        raise ValueError("Use no máximo duas casas decimais.")
    return int((n * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def ler_quantidade(valor):
    try:
        n = int(str(valor or "0").strip())
    except (ValueError, TypeError) as exc:
        raise ValueError("As quantidades devem ser números inteiros.") from exc
    if n < 0:
        raise ValueError("As quantidades não podem ser negativas.")
    return n


async def main(page: ft.Page):
    page.title = "Vendinhas"
    page.scroll = "auto"
    page.padding = ft.Padding(top=20, left=16, right=16, bottom=28)
    page.fonts = {
        "Cursiva": "https://raw.githubusercontent.com/google/fonts/main/ofl/lobstertwo/LobsterTwo-Regular.ttf"
    }

    # Flet 1.0: armazenamento é um serviço separado de Page.
    preferencias = ft.SharedPreferences()

    async def carregar(chave, padrao):
        bruto = await preferencias.get(chave)
        if not bruto:
            return padrao
        try:
            return json.loads(bruto)
        except (ValueError, TypeError):
            return padrao

    # Intencional: catálogo novo começa vazio e não importa produtos fixos antigos.
    produtos = await carregar(CHAVE_PRODUTOS, [])
    vendas = await carregar(CHAVE_VENDAS, [])
    caixa = await carregar(CHAVE_CAIXA, {str(d): 0 for d in DENOMINACOES})
    for d in DENOMINACOES:
        caixa.setdefault(str(d), 0)

    async def salvar():
        await preferencias.set(CHAVE_PRODUTOS, json.dumps(produtos, ensure_ascii=False))
        await preferencias.set(CHAVE_VENDAS, json.dumps(vendas, ensure_ascii=False))
        await preferencias.set(CHAVE_CAIXA, json.dumps(caixa))

    def aviso(mensagem, erro=False):
        page.show_dialog(ft.SnackBar(content=ft.Text(mensagem), bgcolor="#b91c1c" if erro else "#166534"))

    def abrir(dialogo):
        page.show_dialog(dialogo)

    def fechar(dialogo):
        page.pop_dialog()

    def produto_por_id(pid):
        return next((p for p in produtos if p["id"] == pid), None)

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


    # ----------------------------------------------------------
    # NAVEGAÇÃO
    # ----------------------------------------------------------
    def cabecalho(titulo):
        return ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=menu_principal),
            ft.Text(titulo, weight="bold", size=21, expand=True),
        ], spacing=8)

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

    def mostrar_produtos(e=None):
        page.controls.clear()
        page.add(
            cabecalho("Produtos"),
            ft.FilledButton("Novo produto", icon=ft.Icons.ADD, on_click=lambda e: abrir_editor()),
            ft.Divider(),
            catalogo_lista,
        )
        atualizar_catalogo()

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

    menu_principal()


if __name__ == "__main__":
    ft.run(main)
