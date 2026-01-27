import streamlit as st
import pandas as pd
import os
from pathlib import Path
from io import BytesIO
import qrcode

from utils.calculo import calcular_custo_total
from utils.excel import gerar_excel_simples

st.set_page_config(page_title="Custo Peça Piloto", layout="centered")


# -------------------------------
# 🔐 PROTEÇÃO POR SENHA (simples)
# -------------------------------
def check_password():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Sistema Interno")
        st.subheader("Acesso restrito")

        senha = st.text_input("Digite a senha", type="password")

        if st.button("Entrar"):
            if senha == "Murano1234":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta")

        st.stop()


def get_app_url() -> str:
    url = st.secrets.get("APP_URL", "")
    return url.rstrip("/") if url else ""


def gerar_qr_png(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def ler_historico(hist_path: str) -> pd.DataFrame:
    if not os.path.exists(hist_path) or os.path.getsize(hist_path) == 0:
        return pd.DataFrame()

    df = pd.read_csv(hist_path)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    return df


def salvar_historico(linha: dict):
    os.makedirs("data", exist_ok=True)
    hist_path = "data/historico.csv"

    colunas = [
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

    df_novo = pd.DataFrame([linha], columns=colunas)

    if os.path.exists(hist_path) and os.path.getsize(hist_path) > 0:
        try:
            df_antigo = pd.read_csv(hist_path)
            df_antigo = df_antigo.loc[:, ~df_antigo.columns.astype(str).str.startswith("Unnamed")]

            # se estrutura estiver diferente, recria mantendo o antigo só nas colunas esperadas (se existirem)
            if list(df_antigo.columns) != colunas:
                df_antigo = df_antigo.reindex(columns=colunas)

            df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            df_final.to_csv(hist_path, index=False)
        except Exception:
            df_novo.to_csv(hist_path, index=False)
    else:
        df_novo.to_csv(hist_path, index=False)


# -------------------------------
# ✅ Login
# -------------------------------
check_password()


# -------------------------------
# 🧾 Ficha técnica (modo leve via QR)
# URL: ?view=ficha&ref=XXXX
# -------------------------------
params = st.query_params
view = params.get("view", "")
ref_qr = params.get("ref", "")

if view == "ficha" and ref_qr:
    st.title("🧾 Ficha Técnica (rápida)")

    hist_path = "data/historico.csv"
    df = ler_historico(hist_path)

    if df.empty:
        st.error("Histórico vazio. Gere ou adicione uma peça primeiro.")
        st.stop()

    linha = df[df["Referência"].astype(str) == str(ref_qr)]
    if linha.empty:
        st.error("Referência não encontrada no histórico.")
        st.stop()

    item = linha.iloc[-1]

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Referência", str(item["Referência"]))
        st.write(f"**Descrição:** {item.get('Descrição','')}")
    with c2:
        st.metric("Total", f"R$ {float(item.get('Total',0)):.2f}")

    st.divider()
    st.subheader("📌 Resumo de custos")
    r1, r2, r3 = st.columns(3)
    r1.metric("Tecido", f"R$ {float(item.get('Tecido',0)):.2f}")
    r2.metric("Oficina", f"R$ {float(item.get('Oficina',0)):.2f}")
    r3.metric("Lavanderia", f"R$ {float(item.get('Lavanderia',0)):.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Aviamento", f"R$ {float(item.get('Aviamento',0)):.2f}")
    r5.metric("Adicionais", f"R$ {float(item.get('Detalhes (adicionais)',0)):.2f}")
    r6.metric("Despesa fixa", f"R$ {float(item.get('Despesa Fixa',0)):.2f}")

    st.divider()
    st.subheader("📥 Excel simples (desta ficha)")
    excel_buffer = gerar_excel_simples(item.to_dict())
    st.download_button(
        "📥 Baixar Excel",
        data=excel_buffer.getvalue(),
        file_name=f"ficha_{ref_qr}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.stop()


# -------------------------------
# App normal
# -------------------------------
st.title("🧵 Sistema de Custo – Peça Piloto")


# -------------------------------
# 📌 Leitura de tabela (Oficina)
# -------------------------------
@st.cache_data
def carregar_tabela_csv(path_str: str):
    path = Path(path_str)
    if not path.exists():
        return None

    df = pd.read_csv(path)
    for col in ["servico", "valor_min", "valor_max", "nota_ziad"]:
        if col not in df.columns:
            df[col] = "" if col in ["servico", "nota_ziad"] else 0.0

    df["servico"] = df["servico"].fillna("").astype(str).str.strip()
    df["nota_ziad"] = df["nota_ziad"].fillna("").astype(str).str.strip()
    df["valor_min"] = pd.to_numeric(df["valor_min"], errors="coerce").fillna(0.0)
    df["valor_max"] = pd.to_numeric(df["valor_max"], errors="coerce").fillna(0.0)

    df = df[df["servico"].str.len() > 0].reset_index(drop=True)
    return df


df_oficina = carregar_tabela_csv("data/oficina.csv")


# -------------------------------
# Estado da sessão
# -------------------------------
if "oficina_itens" not in st.session_state:
    st.session_state.oficina_itens = []

if "lavanderia_manual_itens" not in st.session_state:
    st.session_state.lavanderia_manual_itens = []

if "adicionais_itens" not in st.session_state:
    st.session_state.adicionais_itens = [
        {"nome": "Cinto", "valor": 0.0},
        {"nome": "Fivela", "valor": 0.0},
        {"nome": "Cordão", "valor": 0.0},
        {"nome": "Lenço", "valor": 0.0},
        {"nome": "Barra dobrada", "valor": 0.0},
    ]


# -------------------------------
# 🧾 Identificação
# -------------------------------
st.subheader("🧾 Identificação da peça")

cA, cB = st.columns(2)
with cA:
    ref = st.text_input("Referência")
    desc = st.text_input("Descrição")
    tamanho = st.text_input("Tamanho piloto")

with cB:
    tipo_peca = st.text_input("Tipo de peça (ex: Calça, Bermuda, Jaqueta)")
    cor_lavagem = st.text_input("Cor / Lavagem")

imagem = st.file_uploader("Imagem da peça piloto", ["jpg", "jpeg", "png"])


# -------------------------------
# 🧵 Tecido
# -------------------------------
st.subheader("🧵 Tecido")
cT1, cT2, cT3 = st.columns([1.2, 1.2, 1.6])

with cT1:
    tecido_nome = st.text_input("Nome do tecido (ex: Denim 12oz)")
    tecido_tipo = st.selectbox("Tipo do tecido", ["Jeans", "Sarja"])

with cT2:
    tecido_preco_m = st.number_input("Preço do tecido (R$/m)", min_value=0.0, value=0.0, step=0.10)
    tecido_consumo_m = st.number_input("Consumo (m)", min_value=0.0, value=0.0, step=0.01)

with cT3:
    tecido_valor = float(tecido_preco_m) * float(tecido_consumo_m)
    st.metric("Custo do tecido (R$)", f"R$ {tecido_valor:.2f}")


# -------------------------------
# 💰 Custos base
# -------------------------------
st.subheader("💰 Custos base")
cb1, cb2, cb3 = st.columns(3)
with cb1:
    aviamentos = st.number_input("Aviamentos (R$)", min_value=0.0, value=3.80, step=0.10)
with cb2:
    acabamento = st.number_input("Acabamento (R$)", min_value=0.0, value=6.50, step=0.10)
with cb3:
    despesa_fixa = st.number_input("Despesa fixa (R$)", min_value=0.0, value=5.50, step=0.10)


# -------------------------------
# Oficina por tabela (sem repetir)
# -------------------------------
def ui_somar_servicos(df: pd.DataFrame, state_key: str, prefix: str):
    if df is None:
        st.warning(f"Tabela não encontrada: data/{prefix}.csv")
        return 0.0

    itens = st.session_state[state_key]
    selecionados = {i["servico"] for i in itens}
    opcoes = [s for s in df["servico"].tolist() if s not in selecionados]

    colS1, colS2 = st.columns([3, 1])
    with colS1:
        escolhido = st.selectbox(
            "Adicionar serviço",
            options=["(selecione)"] + opcoes,
            index=0,
            key=f"{prefix}_select"
        )
    with colS2:
        add = st.button("Adicionar", use_container_width=True, key=f"{prefix}_add_btn", disabled=(escolhido == "(selecione)"))

    if add and escolhido != "(selecione)":
        linha_df = df[df["servico"] == escolhido].iloc[0].to_dict()
        valor_sugerido = float(linha_df.get("valor_min", 0.0))

        itens.append({
            "servico": str(linha_df.get("servico", "")),
            "valor_min": float(linha_df.get("valor_min", 0.0)),
            "valor_max": float(linha_df.get("valor_max", float(linha_df.get("valor_min", 0.0)))),
            "nota_ziad": str(linha_df.get("nota_ziad", "")),
            "valor_real": valor_sugerido
        })
        st.session_state[state_key] = itens
        st.rerun()

    total_real = 0.0

    if itens:
        st.markdown("### Serviços adicionados")

        for idx, item in enumerate(itens):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])

                with c1:
                    st.write(f"**{item['servico']}**")
                    if item.get("nota_ziad"):
                        st.caption(f"🟥 Nota: {item['nota_ziad']}")

                    vmin = float(item["valor_min"])
                    vmax = float(item["valor_max"])
                    if vmin != vmax:
                        st.caption(f"Tabela: R$ {vmin:.2f} – R$ {vmax:.2f}")
                    else:
                        st.caption(f"Tabela: R$ {vmin:.2f}")

                with c2:
                    novo = st.number_input(
                        "Valor real (R$)",
                        min_value=0.0,
                        value=float(item["valor_real"]),
                        step=0.10,
                        key=f"{prefix}_real_{idx}"
                    )
                    itens[idx]["valor_real"] = float(novo)

                with c3:
                    if st.button("Remover", key=f"{prefix}_rem_{idx}", use_container_width=True):
                        itens.pop(idx)
                        st.session_state[state_key] = itens
                        st.rerun()

            total_real += float(itens[idx]["valor_real"])

    return float(total_real)


# -------------------------------
# 🏭 Oficina
# -------------------------------
st.subheader("🏭 Oficina")
total_oficina_real = ui_somar_servicos(df_oficina, "oficina_itens", "oficina")
st.metric("Total oficina (R$)", f"R$ {total_oficina_real:.2f}")


# -------------------------------
# 🧼 Lavanderia (manual)
# -------------------------------
st.subheader("🧼 Lavanderia (valores manuais)")

col_l1, col_l2, col_l3 = st.columns([2.2, 1.2, 1])
with col_l1:
    lav_nome = st.text_input("Nome do serviço", placeholder="Ex: Stone wash, Destroyed...", key="lav_nome")
with col_l2:
    lav_valor = st.number_input("Valor (R$)", min_value=0.0, value=0.0, step=0.10, key="lav_valor", disabled=not lav_nome.strip())
with col_l3:
    lav_add = st.button("Adicionar", use_container_width=True, key="lav_add", disabled=not lav_nome.strip())

nomes_lav = {i["nome"].strip().lower() for i in st.session_state.lavanderia_manual_itens}
if lav_add:
    nome_limpo = lav_nome.strip()
    if nome_limpo.lower() in nomes_lav:
        st.warning("Esse serviço já foi adicionado.")
    else:
        st.session_state.lavanderia_manual_itens.append({"nome": nome_limpo, "valor": float(lav_valor)})
        st.rerun()

cols_lav = st.columns(3)
for idx, item in enumerate(st.session_state.lavanderia_manual_itens):
    col = cols_lav[idx % 3]
    with col:
        with st.container(border=True):
            st.write(f"**{item['nome']}**")
            val = st.number_input("R$", min_value=0.0, value=float(item["valor"]), step=0.10, key=f"lav_item_{idx}", label_visibility="collapsed")
            st.session_state.lavanderia_manual_itens[idx]["valor"] = float(val)

            if st.button("Remover", key=f"lav_rem_{idx}", use_container_width=True):
                st.session_state.lavanderia_manual_itens.pop(idx)
                st.rerun()

total_lavanderia = float(sum(i["valor"] for i in st.session_state.lavanderia_manual_itens))
st.metric("Total lavanderia (R$)", f"R$ {total_lavanderia:.2f}")


# -------------------------------
# ➕ Adicionais
# -------------------------------
st.subheader("➕ Adicionais (valores manuais)")

col_a1, col_a2, col_a3 = st.columns([2.2, 1.2, 1])
with col_a1:
    novo_nome = st.text_input("Nome do adicional", placeholder="Ex: Zíper, Etiqueta...", key="add_nome")
with col_a2:
    novo_valor = st.number_input("Valor (R$)", min_value=0.0, value=0.0, step=0.10, key="add_valor", disabled=not novo_nome.strip())
with col_a3:
    add_novo = st.button("Adicionar", use_container_width=True, key="add_btn", disabled=not novo_nome.strip())

nomes_existentes = {i["nome"].strip().lower() for i in st.session_state.adicionais_itens}
if add_novo:
    nome_limpo = novo_nome.strip()
    if nome_limpo.lower() in nomes_existentes:
        st.warning("Esse adicional já existe.")
    else:
        st.session_state.adicionais_itens.append({"nome": nome_limpo, "valor": float(novo_valor)})
        st.rerun()

cols = st.columns(3)
for idx, item in enumerate(st.session_state.adicionais_itens):
    col = cols[idx % 3]
    with col:
        with st.container(border=True):
            st.write(f"**{item['nome']}**")
            val = st.number_input("R$", min_value=0.0, value=float(item["valor"]), step=0.10, key=f"ad_val_{idx}", label_visibility="collapsed")
            st.session_state.adicionais_itens[idx]["valor"] = float(val)

            if idx >= 5:
                if st.button("Remover", key=f"ad_rem_{idx}", use_container_width=True):
                    st.session_state.adicionais_itens.pop(idx)
                    st.rerun()

total_adicionais = float(sum(i["valor"] for i in st.session_state.adicionais_itens))
st.metric("Total adicionais (R$)", f"R$ {total_adicionais:.2f}")


# -------------------------------
# 📌 Resumo + Total
# -------------------------------
st.divider()
st.subheader("📌 Resumo final")

aviamento_total = float(aviamentos) + float(acabamento)  # simplifica (1 coluna no excel)
custos_dict = {
    "Tecido": float(tecido_valor),
    "Oficina": float(total_oficina_real),
    "Lavanderia": float(total_lavanderia),
    "Aviamento": float(aviamento_total),
    "Detalhes (adicionais)": float(total_adicionais),
    "Despesa Fixa": float(despesa_fixa),
}

total_geral = float(sum(custos_dict.values()))
_ = calcular_custo_total(custos_dict)

with st.container(border=True):
    r1, r2, r3 = st.columns(3)
    r1.metric("Tecido", f"R$ {custos_dict['Tecido']:.2f}")
    r2.metric("Oficina", f"R$ {custos_dict['Oficina']:.2f}")
    r3.metric("Lavanderia", f"R$ {custos_dict['Lavanderia']:.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Aviamento", f"R$ {custos_dict['Aviamento']:.2f}")
    r5.metric("Adicionais", f"R$ {custos_dict['Detalhes (adicionais)']:.2f}")
    r6.metric("Despesa fixa", f"R$ {custos_dict['Despesa Fixa']:.2f}")

    st.divider()
    st.metric("💰 TOTAL GERAL", f"R$ {total_geral:.2f}")


# -------------------------------
# ✅ Botões: Adicionar / Excel / QR
# -------------------------------
st.divider()
b1, b2, b3 = st.columns(3)

with b1:
    btn_add_hist = st.button("➕ Adicionar ao histórico", use_container_width=True)

with b2:
    btn_excel = st.button("📥 Gerar Excel", type="primary", use_container_width=True)

with b3:
    btn_qr = st.button("🧾 Gerar QR (Ficha)", use_container_width=True)

# Linha (padrão da sua planilha)
linha_padrao = {
    "Referência": ref.strip(),
    "Descrição": desc.strip(),
    "Tecido (R$/m)": round(float(tecido_preco_m), 2),
    "Consumo (m)": round(float(tecido_consumo_m), 3),
    "Custo do tecido": round(float(tecido_valor), 2),
    "Oficina": round(float(total_oficina_real), 2),
    "Lavanderia": round(float(total_lavanderia), 2),
    "Aviamento": round(float(aviamentos + acabamento), 2),
    "Detalhes (adicionais)": round(float(total_adicionais), 2),
    "Despesa Fixa": round(float(despesa_fixa), 2),
    "Total": round(float(total_geral), 2),
}

if btn_add_hist:
    if not linha_padrao["Referência"]:
        st.error("Preencha a Referência antes de adicionar ao histórico.")
    else:
        salvar_historico(linha_padrao)
        st.success("✅ Adicionado ao histórico!")

if btn_excel:
    if not linha_padrao["Referência"]:
        st.error("Preencha a Referência antes de gerar o Excel.")
    else:
        excel_buffer = gerar_excel_simples(linha_padrao)
        st.success("✅ Excel pronto!")

        st.download_button(
            "📥 Baixar Excel",
            data=excel_buffer.getvalue(),
            file_name=f"custo_{linha_padrao['Referência']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

if btn_qr:
    app_url = get_app_url()
    if not app_url:
        st.error('Defina APP_URL nos Secrets (ex: "https://seuapp.streamlit.app").')
    elif not linha_padrao["Referência"]:
        st.error("Preencha a Referência antes de gerar o QR.")
    else:
        # Gera QR para ficha rápida
        url = f"{app_url}/?view=ficha&ref={linha_padrao['Referência']}"
        png = gerar_qr_png(url)

        st.image(png, width=220)
        st.download_button(
            "⬇️ Baixar QR (PNG)",
            data=png,
            file_name=f"qr_{linha_padrao['Referência']}.png",
            mime="image/png",
            use_container_width=True
        )
        st.caption("Link da ficha (para testar):")
        st.code(url)


# -------------------------------
# 📚 Histórico (exibição)
# -------------------------------
st.divider()
st.subheader("📚 Histórico de Peças")

hist_path = "data/historico.csv"
df_hist = ler_historico(hist_path)

if df_hist.empty:
    st.info("Ainda não há histórico. Adicione uma peça ou gere o Excel para registrar.")
else:
    st.dataframe(df_hist, use_container_width=True)
