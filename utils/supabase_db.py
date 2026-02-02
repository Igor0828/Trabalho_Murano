import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Colunas "bonitas" que você usa no app/Excel
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

# Mapeamento App -> Banco (de acordo com seu SQL!)
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


def salvar_historico(linha: dict) -> None:
    """
    Insere 1 registro no Supabase (tabela public.historico_pecas).
    """
    sb = _sb()

    payload = {}
    for app_col, db_col in APP_TO_DB.items():
        payload[db_col] = linha.get(app_col, None)

    # Garantias mínimas
    payload["referencia"] = str(payload.get("referencia", "")).strip()
    payload["descricao"] = str(payload.get("descricao", "")).strip()

    if not payload["referencia"]:
        raise ValueError("Referência vazia.")

    # Números como float (evita erro silencioso com string/vazio)
    num_cols = [
        "tecido_rs_m", "consumo_m", "custo_tecido",
        "oficina", "lavanderia", "aviamento",
        "adicionais", "despesa_fixa", "total"
    ]
    for c in num_cols:
        v = payload.get(c, 0)
        try:
            payload[c] = float(v) if v is not None else 0.0
        except Exception:
            payload[c] = 0.0

    sb.table("historico_pecas").insert(payload).execute()

    # Atualiza cache de leitura
    st.cache_data.clear()


@st.cache_data(ttl=20)
def ler_historico(limit: int = 5000) -> pd.DataFrame:
    """
    Lê o histórico do Supabase (mais recentes primeiro).
    Retorna DataFrame com as colunas no formato do app.
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

    # DB -> App
    df_out = pd.DataFrame()
    for db_col, app_col in DB_TO_APP.items():
        df_out[app_col] = df[db_col] if db_col in df.columns else None

    # Ordena colunas
    df_out = df_out.reindex(columns=COLUNAS_PADRAO)

    # Tipagem numérica
    num_cols_app = [
        "Tecido (R$/m)", "Consumo (m)", "Custo do tecido",
        "Oficina", "Lavanderia", "Aviamento",
        "Detalhes (adicionais)", "Despesa Fixa", "Total"
    ]
    for c in num_cols_app:
        df_out[c] = pd.to_numeric(df_out[c], errors="coerce").fillna(0.0)

    df_out["Referência"] = df_out["Referência"].fillna("").astype(str)
    df_out["Descrição"] = df_out["Descrição"].fillna("").astype(str)

    return df_out
