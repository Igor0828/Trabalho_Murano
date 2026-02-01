import streamlit as st
import pandas as pd
from supabase import create_client, Client

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

# Mapeamento: coluna do app -> coluna do banco
APP_TO_DB = {
    "Referência": "referencia",
    "Descrição": "descricao",
    "Tecido (R$/m)": "tecido_rs_m",
    "Consumo (m)": "consumo_m",
    "Custo do tecido": "custo_tecido",
    "Oficina": "oficina",
    "Lavanderia": "lavanderia",
    "Aviamento": "aviamento",
    "Detalhes (adicionais)": "adicionais",
    "Despesa Fixa": "despesa_fixa",
    "Total": "total",
}

DB_TO_APP = {v: k for k, v in APP_TO_DB.items()}


@st.cache_resource
def _sb() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def append_row(linha: dict) -> None:
    """
    Insere 1 registro na tabela historico_pecas.
    """
    sb = _sb()

    payload = {}
    for app_col, db_col in APP_TO_DB.items():
        payload[db_col] = linha.get(app_col, None)

    # Garantias mínimas
    payload["referencia"] = str(payload.get("referencia", "")).strip()
    if not payload["referencia"]:
        raise ValueError("Referência vazia.")

    sb.table("historico_pecas").insert(payload).execute()

    # força atualizar cache de leitura
    st.cache_data.clear()


@st.cache_data(ttl=20)
def read_all(limit: int = 5000) -> pd.DataFrame:
    """
    Lê o histórico (até 'limit' linhas), mais recentes primeiro.
    Cache curto para reduzir chamadas.
    """
    sb = _sb()

    resp = (
        sb.table("historico_pecas")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    data = resp.data or []
    if not data:
        return pd.DataFrame(columns=COLUNAS_PADRAO)

    df = pd.DataFrame(data)

    # Converte DB -> App
    df_out = pd.DataFrame()
    for db_col, app_col in DB_TO_APP.items():
        if db_col in df.columns:
            df_out[app_col] = df[db_col]
        else:
            df_out[app_col] = None

    # Garante ordem
    df_out = df_out.reindex(columns=COLUNAS_PADRAO)

    # Tipos numéricos
    num_cols = [
        "Tecido (R$/m)", "Consumo (m)", "Custo do tecido",
        "Oficina", "Lavanderia", "Aviamento",
        "Detalhes (adicionais)", "Despesa Fixa", "Total"
    ]
    for c in num_cols:
        df_out[c] = pd.to_numeric(df_out[c], errors="coerce").fillna(0.0)

    # Strings
    df_out["Referência"] = df_out["Referência"].fillna("").astype(str)
    df_out["Descrição"] = df_out["Descrição"].fillna("").astype(str)

    return df_out
