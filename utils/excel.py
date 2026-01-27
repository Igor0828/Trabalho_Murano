import pandas as pd
from io import BytesIO

COLUNAS_PADRAO = [
    "Referência",
    "Descrição",
    "Tecido (R$/m)",
    "Consumo (m)",
    "Custo do tecido",
    "Oficina",
    "Lavanderia",
    "Aviamento",
    "Detalhes (adicionais)",
    "Despesa Fixa",
    "Total",
]

def gerar_excel_simples(linha: dict) -> BytesIO:
    buffer = BytesIO()
    df = pd.DataFrame([linha], columns=COLUNAS_PADRAO)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Custos")

    buffer.seek(0)
    return buffer


def gerar_excel_multiplos(df: pd.DataFrame) -> BytesIO:
    """
    Exporta várias linhas do histórico para Excel.
    """
    buffer = BytesIO()

    # garante ordem e colunas
    df_out = df.reindex(columns=COLUNAS_PADRAO)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_out.to_excel(writer, index=False, sheet_name="Custos")

    buffer.seek(0)
    return buffer
