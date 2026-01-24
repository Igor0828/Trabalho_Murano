import pandas as pd
from io import BytesIO

def gerar_excel(dados_peca, custos, total, oficina_itens=None, adicionais=None):
    buffer = BytesIO()

    # Aba: Peça
    df_peca = pd.DataFrame({
        "Campo": list(dados_peca.keys()),
        "Valor": list(dados_peca.values())
    })

    # Aba: Custos (resumo)
    df_custos = pd.DataFrame({
        "Item": list(custos.keys()),
        "Valor (R$)": list(custos.values())
    })

    df_total = pd.DataFrame({
        "Resumo": ["Custo Total"],
        "Valor (R$)": [total]
    })

    # Aba: Oficina (itens)
    if oficina_itens is None:
        oficina_itens = []
    df_oficina = pd.DataFrame(oficina_itens) if oficina_itens else pd.DataFrame(
        columns=["servico", "valor_min", "valor_max", "nota_ziad", "valor_real"]
    )
    # renomeia colunas pra ficar bonito
    if not df_oficina.empty:
        df_oficina = df_oficina.rename(columns={
            "servico": "Serviço",
            "valor_min": "Tabela (mín)",
            "valor_max": "Tabela (máx)",
            "nota_ziad": "Nota Ziad",
            "valor_real": "Valor real",
        })

    # Aba: Adicionais (detalhado)
    if adicionais is None:
        adicionais = {}
    df_adicionais = pd.DataFrame({
        "Adicional": list(adicionais.keys()),
        "Valor (R$)": list(adicionais.values())
    })

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_peca.to_excel(writer, index=False, sheet_name="Peça")
        df_custos.to_excel(writer, index=False, sheet_name="Custos")
        df_total.to_excel(writer, index=False, sheet_name="Resumo")
        df_oficina.to_excel(writer, index=False, sheet_name="Oficina")
        df_adicionais.to_excel(writer, index=False, sheet_name="Adicionais")

    return buffer
