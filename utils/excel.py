import pandas as pd
from io import BytesIO


def gerar_excel(
    dados_peca,
    custos,
    total,
    oficina_itens=None,
    lavanderia_itens=None,
    adicionais=None
):
    buffer = BytesIO()

    df_peca = pd.DataFrame({
        "Campo": list(dados_peca.keys()),
        "Valor": list(dados_peca.values())
    })

    df_custos = pd.DataFrame({
        "Item": list(custos.keys()),
        "Valor (R$)": list(custos.values())
    })

    df_resumo = pd.DataFrame({
        "Resumo": ["Custo Total"],
        "Valor (R$)": [total]
    })

    # Oficina
    if oficina_itens is None:
        oficina_itens = []
    df_oficina = pd.DataFrame(oficina_itens) if oficina_itens else pd.DataFrame(
        columns=["servico", "valor_min", "valor_max", "nota_ziad", "valor_real"]
    )
    if not df_oficina.empty:
        df_oficina = df_oficina.rename(columns={
            "servico": "Serviço",
            "valor_min": "Tabela (mín)",
            "valor_max": "Tabela (máx)",
            "nota_ziad": "Nota",
            "valor_real": "Valor real",
        })

    # Lavanderia (manual adaptada no app para esse formato)
    if lavanderia_itens is None:
        lavanderia_itens = []
    df_lav = pd.DataFrame(lavanderia_itens) if lavanderia_itens else pd.DataFrame(
        columns=["servico", "valor_min", "valor_max", "nota_ziad", "valor_real"]
    )
    if not df_lav.empty:
        df_lav = df_lav.rename(columns={
            "servico": "Serviço",
            "valor_min": "Tabela (mín)",
            "valor_max": "Tabela (máx)",
            "nota_ziad": "Nota",
            "valor_real": "Valor real",
        })

    # Adicionais
    if adicionais is None:
        adicionais = {}
    df_adicionais = pd.DataFrame({
        "Adicional": list(adicionais.keys()),
        "Valor (R$)": list(adicionais.values())
    })

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_peca.to_excel(writer, index=False, sheet_name="Peça")
        df_custos.to_excel(writer, index=False, sheet_name="Custos")
        df_resumo.to_excel(writer, index=False, sheet_name="Resumo")
        df_oficina.to_excel(writer, index=False, sheet_name="Oficina")
        df_lav.to_excel(writer, index=False, sheet_name="Lavanderia")
        df_adicionais.to_excel(writer, index=False, sheet_name="Adicionais")

    return buffer
