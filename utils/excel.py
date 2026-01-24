import pandas as pd
from io import BytesIO

def gerar_excel(dados_peca, custos, total, parcelas, valor_parcela):
    buffer = BytesIO()

    df_custos = pd.DataFrame({
        "Item": list(custos.keys()),
        "Valor (R$)": list(custos.values())
    })

    resumo = pd.DataFrame({
        "Descrição": ["Custo Total", "Parcelas", "Valor por Parcela"],
        "Valor": [total, parcelas, valor_parcela]
    })

    info = pd.DataFrame({
        "Campo": dados_peca.keys(),
        "Valor": dados_peca.values()
    })

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        info.to_excel(writer, index=False, sheet_name="Peça")
        df_custos.to_excel(writer, index=False, sheet_name="Custos")
        resumo.to_excel(writer, index=False, sheet_name="Resumo")

    return buffer
