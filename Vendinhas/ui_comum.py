import flet as ft

ALTURA_BOTAO = 50
LARGURA_MAXIMA = 420
MARGEM_DIALOGO = 16


def aviso(page, mensagem, erro=False):
    page.show_dialog(ft.SnackBar(content=ft.Text(mensagem), bgcolor="#b91c1c" if erro else "#166534"))


def _layout(page):
    """Guarda, por página, o bloco da tela atual e o diálogo ajustável aberto."""
    if not isinstance(page.data, dict):
        page.data = {}
    return page.data.setdefault("layout", {"bloco": None, "dialogo": None})


def abrir(page, dialogo):
    layout = _layout(page)
    if layout["dialogo"] and layout["dialogo"][0] is not dialogo:
        layout["dialogo"] = None
    page.show_dialog(dialogo)


def fechar(page, dialogo):
    _layout(page)["dialogo"] = None
    page.pop_dialog()


def cabecalho(titulo, voltar):
    return ft.Row([
        ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar),
        ft.Text(titulo, weight="bold", size=21, expand=True),
    ], spacing=8)


def botao(texto, icone, ao_clicar, destaque=True):
    """Botão principal padronizado: mesma altura e largura total do bloco."""
    classe = ft.FilledButton if destaque else ft.OutlinedButton
    return classe(texto, icon=icone, on_click=ao_clicar, height=ALTURA_BOTAO)


def mostrar(page, *controles):
    """Troca o conteúdo da página por uma coluna centralizada e com largura limitada."""
    bloco = ft.Container(
        width=_largura_tela(page),
        content=ft.Column(list(controles), horizontal_alignment=ft.CrossAxisAlignment.STRETCH, spacing=12),
    )
    _layout(page)["bloco"] = bloco
    page.controls.clear()
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(bloco)
    page.update()


def _largura_tela(page):
    return min((page.width or LARGURA_MAXIMA) - 32, LARGURA_MAXIMA)


def preparar_dialogo(page, dialogo, largura_maxima=400, altura=None):
    """Ajusta o diálogo à tela atual (margens menores, largura e altura proporcionais)."""
    _layout(page)["dialogo"] = (dialogo, largura_maxima, altura)
    _medir_dialogo(page, dialogo, largura_maxima, altura)


def _medir_dialogo(page, dialogo, largura_maxima, altura):
    dialogo.inset_padding = ft.Padding(left=MARGEM_DIALOGO, right=MARGEM_DIALOGO, top=24, bottom=24)
    dialogo.content_padding = ft.Padding(left=16, right=16, top=12, bottom=0)
    dialogo.content.width = min((page.width or largura_maxima) - 2 * MARGEM_DIALOGO - 32, largura_maxima)
    if altura:
        dialogo.content.height = min(altura, (page.height or altura) * 0.6)


def ao_redimensionar(page):
    """Reajusta a tela e o diálogo abertos quando a janela muda (ex.: girar o celular).

    Só muda larguras e alturas; os controles continuam os mesmos, então nada
    que o usuário já digitou é perdido.
    """
    def tratar(e=None):
        layout = _layout(page)
        if layout["bloco"] is not None:
            layout["bloco"].width = _largura_tela(page)
        if layout["dialogo"]:
            _medir_dialogo(page, *layout["dialogo"])
        page.update()

    page.on_resize = tratar
