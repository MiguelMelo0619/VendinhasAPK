```py
meu_app/
  main.py          # ponto de entrada: configura a página e monta as telas
  constantes.py    # chaves de armazenamento e denominações do caixa
  formatacao.py    # moeda, ler_preco, ler_quantidade
  estado.py        # dados (produtos, vendas, caixa) e persistência
  ui_comum.py      # aviso, abrir, fechar, cabecalho
  telas/
    menu.py        # menu principal
    produtos.py    # cadastro, edição e exclusão de produtos
    vendas.py      # registro, desfazer, zerar e resumo de vendas
    caixa.py       # carteira e movimentação do caixa
```
