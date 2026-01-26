import pandas as pd
from io import BytesIO


def gerar_excel_simples(linha: dict) -> BytesIO:
    """
    Gera um Excel simples com UMA aba e UMA linha no formato:
    Referência | Descrição | Tecido | Oficina | Lavanderia | Aviamento | Detalhes (adicionais) | Despesa Fixa | Total
    """
    buffer = BytesIO()

    colunas = [
        "Referência",
        "Descrição",
        "Tecido",
        "Oficina",
        "Lavanderia",
        "Aviamento",
        "Detalhes (adicionais)",
        "Despesa Fixa",
        "Total",
    ]

    df = pd.DataFrame([linha], columns=colunas)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Custos")

    buffer.seek(0)
    return buffer
