from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


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
