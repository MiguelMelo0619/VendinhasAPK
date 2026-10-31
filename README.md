# Marcelinho Lanches

App de cadastro de produtos, vendas e controle de caixa, feito em Python com [Flet](https://flet.dev) (1.0 ou superior).

## Instalação

windows
```bash
python -m venv .venv
.venv\Scripts\activate
pip install flet
```

linux/mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flet
```

## Rodar no PC

```bash
flet run meu_app/main.py
```

Abre uma janela do app. Sem o `flet` no PATH, use `python meu_app/main.py`.

## Rodar no celular

1. Instale o app **Flet** no celular (Play Store ou App Store).
2. Com o PC e o celular na mesma rede Wi-Fi, rode:

```bash
flet run --android meu_app/main.py
```

(use `--ios` no iPhone)

3. Escaneie o QR code exibido no terminal pelo app Flet.
