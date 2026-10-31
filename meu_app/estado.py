import json

import flet as ft

from constantes import CHAVE_CAIXA, CHAVE_PRODUTOS, CHAVE_VENDAS, DENOMINACOES


class Estado:
    """Dados do app (produtos, vendas, caixa) e sua persistência.

    As coleções são sempre alteradas no lugar, nunca reatribuídas, para que
    todas as telas enxerguem os mesmos objetos.
    """

    def __init__(self):
        # Flet 1.0: armazenamento é um serviço separado de Page.
        self.preferencias = ft.SharedPreferences()
        self.produtos = []
        self.vendas = []
        self.caixa = {}

    async def carregar(self, chave, padrao):
        bruto = await self.preferencias.get(chave)
        if not bruto:
            return padrao
        try:
            return json.loads(bruto)
        except (ValueError, TypeError):
            return padrao

    async def carregar_tudo(self):
        # Intencional: catálogo novo começa vazio e não importa produtos fixos antigos.
        self.produtos = await self.carregar(CHAVE_PRODUTOS, [])
        self.vendas = await self.carregar(CHAVE_VENDAS, [])
        self.caixa = await self.carregar(CHAVE_CAIXA, {str(d): 0 for d in DENOMINACOES})
        for d in DENOMINACOES:
            self.caixa.setdefault(str(d), 0)

    async def salvar(self):
        await self.preferencias.set(CHAVE_PRODUTOS, json.dumps(self.produtos, ensure_ascii=False))
        await self.preferencias.set(CHAVE_VENDAS, json.dumps(self.vendas, ensure_ascii=False))
        await self.preferencias.set(CHAVE_CAIXA, json.dumps(self.caixa))

    def produto_por_id(self, pid):
        return next((p for p in self.produtos if p["id"] == pid), None)
