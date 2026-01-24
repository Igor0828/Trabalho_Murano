import streamlit as st
import pandas as pd
import os
from pathlib import Path

from utils.calculo import calcular_custo_total
from utils.excel import gerar_excel

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

check_password()

# -------------------------------
# 🧵 APP PRINCIPAL
# -------------------------------
st.set_page_config(page_title="Custo Peça Piloto", layout="centered")
st.title("🧵 Sistema de Custo – Peça Piloto")

# -------------------------------
# 📌 Tabela da oficina (CSV)
# -------------------------------
@st.cache_data
def carregar_tabela_oficina():
    path = Path("data/oficina.csv")
    if not path.exists():
        return None

    df = pd.read_csv(path)
    # normaliza
    for col in ["valor_min", "valor_max"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["nota_ziad"] = df.get("nota_ziad", "").fillna("").astype(str)
    df["servico"] = df["servico"].astype(str)
    return df

df_oficina = carregar_tabela_oficina()

# Estado: serviços selecionados (sem repetir)
if "oficina_itens" not in st.session_state:
    st.session_state.oficina_itens = []

# -------------------------------
# 💰 Preços Fixos (por enquanto mantém)
# -------------------------------
st.subheader("💰 Custos base (preços fixos / manuais)")

col1, col2, col3 = st.columns(3)
with col1:
    aviamentos = st.number_input("Aviamentos (R$)", min_value=0.0, value=10.8, step=0.10)
    linha = st.number_input("Linha (R$)", min_value=0.0, value=2.4, step=0.10)
with col2:
    lavanderia = st.number_input("Lavanderia (R$)", min_value=0.0, value=18.0, step=0.10)
    acabamento = st.number_input("Acabamento (R$)", min_value=0.0, value=6.5, step=0.10)
with col3:
    indiretos = st.number_input("Custos indiretos (R$)", min_value=0.0, value=15.0, step=0.10)

# -------------------------------
# 🧾 Identificação + Tecido + Foto
# -------------------------------
st.subheader("🧾 Identificação da peça")

cA, cB = st.columns(2)
with cA:
    ref = st.text_input("Referência")
    desc = st.text_input("Descrição")
    tamanho = st.text_input("Tamanho piloto")
with cB:
    tipo_peca = st.text_input("Tipo de peça (ex: Calça, Bermuda, Jaqueta)")
    tecido_nome = st.text_input("Nome do tecido (ex: Denim 12oz)")
    tecido_tipo = st.selectbox("Tipo do tecido", ["Jeans", "Sarja"])

cor_lavagem = st.text_input("Cor / Lavagem")
imagem = st.file_uploader("Imagem da peça piloto", ["jpg", "jpeg", "png"])

# -------------------------------
# 🧵 Custo variável (tecido)
# -------------------------------
st.subheader("🧵 Custo variável")
tecido_valor = st.number_input("Tecido (R$)", min_value=0.0, value=0.0, step=0.10)

# -------------------------------
# 🏭 Oficina (somar serviços, sem repetir)
# -------------------------------
st.subheader("🏭 Oficina (serviços)")

if df_oficina is None:
    st.warning("Arquivo data/oficina.csv não encontrado. Crie o arquivo para usar a oficina.")
else:
    selecionados = {i["servico"] for i in st.session_state.oficina_itens}
    opcoes = [s for s in df_oficina["servico"].tolist() if s not in selecionados]

    colS1, colS2 = st.columns([3, 1])
    with colS1:
        servico_escolhido = st.selectbox("Adicionar serviço", options=["(selecione)"] + opcoes, index=0)
    with colS2:
        adicionar = st.button("Adicionar", use_container_width=True)

    if adicionar and servico_escolhido != "(selecione)":
        linha_df = df_oficina[df_oficina["servico"] == servico_escolhido].iloc[0].to_dict()
        valor_sugerido = float(linha_df.get("valor_min", 0.0))  # se for faixa, começa pelo mínimo

        st.session_state.oficina_itens.append({
            "servico": str(linha_df["servico"]),
            "valor_min": float(linha_df.get("valor_min", 0.0)),
            "valor_max": float(linha_df.get("valor_max", linha_df.get("valor_min", 0.0))),
            "nota_ziad": str(linha_df.get("nota_ziad", "")),
            "valor_real": valor_sugerido,  # editável
        })
        st.rerun()

    if st.session_state.oficina_itens:
        st.markdown("### Serviços adicionados")

        total_tabela_min = 0.0
        total_tabela_max = 0.0
        total_real = 0.0

        for idx, item in enumerate(st.session_state.oficina_itens):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])

                with c1:
                    st.write(f"**{item['servico']}**")
                    if item["nota_ziad"]:
                        st.caption(f"🟥 Nota Ziad: {item['nota_ziad']}")

                    if item["valor_min"] != item["valor_max"]:
                        st.caption(f"Tabela: R$ {item['valor_min']:.2f} – R$ {item['valor_max']:.2f}")
                    else:
                        st.caption(f"Tabela: R$ {item['valor_min']:.2f}")

                with c2:
                    novo_valor = st.number_input(
                        "Valor real (R$)",
                        min_value=0.0,
                        value=float(item["valor_real"]),
                        step=0.10,
                        key=f"oficina_valor_real_{idx}"
                    )
                    st.session_state.oficina_itens[idx]["valor_real"] = float(novo_valor)

                with c3:
                    if st.button("Remover", key=f"oficina_remover_{idx}", use_container_width=True):
                        st.session_state.oficina_itens.pop(idx)
                        st.rerun()

            total_tabela_min += float(item["valor_min"])
            total_tabela_max += float(item["valor_max"])
            total_real += float(item["valor_real"])

        st.markdown("### Totais da Oficina")
        t1, t2, t3 = st.columns(3)
        t1.metric("Tabela (mín)", f"R$ {total_tabela_min:.2f}")
        t2.metric("Tabela (máx)", f"R$ {total_tabela_max:.2f}")
        t3.metric("Real", f"R$ {total_real:.2f}")
    else:
        st.info("Adicione serviços da oficina para compor o custo de costura.")

# Total oficina real (mesmo se não tiver CSV)
total_oficina_real = sum(i.get("valor_real", 0.0) for i in st.session_state.oficina_itens)

# -------------------------------
# ➕ Adicionais (manuais, variáveis)
# -------------------------------
st.subheader("➕ Adicionais (valores manuais)")

a1, a2, a3 = st.columns(3)
with a1:
    add_cinto = st.number_input("Cinto (R$)", min_value=0.0, value=0.0, step=0.10)
    add_fivela = st.number_input("Fivela (R$)", min_value=0.0, value=0.0, step=0.10)
with a2:
    add_cordao = st.number_input("Cordão (R$)", min_value=0.0, value=0.0, step=0.10)
    add_lenco = st.number_input("Lenço (R$)", min_value=0.0, value=0.0, step=0.10)
with a3:
    add_barra = st.number_input("Barra dobrada (R$)", min_value=0.0, value=0.0, step=0.10)

obs_detalhes = st.text_area("Observações (detalhes da peça)", height=90)

total_adicionais = add_cinto + add_fivela + add_cordao + add_lenco + add_barra

# -------------------------------
# ✅ Gerar resultado + Excel
# -------------------------------
st.divider()
gerar = st.button("✅ Gerar custo e Excel", type="primary", use_container_width=True)

if gerar:
    custos = {
        "Tecido": tecido_valor,
        "Aviamentos": aviamentos,
        "Linha": linha,
        "Lavanderia": lavanderia,
        "Acabamento": acabamento,
        "Custos indiretos": indiretos,
        "Oficina (real)": total_oficina_real,
        "Adicionais (total)": total_adicionais,
    }

    total = calcular_custo_total(custos)

    st.success(f"💰 Custo total: R$ {total:.2f}")

    if imagem:
        st.image(imagem, width=320)

    dados_peca = {
        "Referência": ref,
        "Descrição": desc,
        "Tipo de peça": tipo_peca,
        "Tamanho piloto": tamanho,
        "Tecido (nome)": tecido_nome,
        "Tecido (tipo)": tecido_tipo,
        "Cor/Lavagem": cor_lavagem,
        "Observações": obs_detalhes,
    }

    # Também exporta os itens da oficina e adicionais detalhados para o Excel
    oficina_itens = st.session_state.oficina_itens
    adicionais = {
        "Cinto": add_cinto,
        "Fivela": add_fivela,
        "Cordão": add_cordao,
        "Lenço": add_lenco,
        "Barra dobrada": add_barra,
    }

    excel_buffer = gerar_excel(
        dados_peca=dados_peca,
        custos=custos,
        total=total,
        oficina_itens=oficina_itens,
        adicionais=adicionais,
    )

    st.download_button(
        "📥 Baixar Excel",
        data=excel_buffer.getvalue(),
        file_name="custo_peca_piloto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # -------------------------------
    # 📚 Histórico
    # -------------------------------
    os.makedirs("data", exist_ok=True)
    hist_path = "data/historico.csv"

    nova_linha = pd.DataFrame([{
        "Referência": ref,
        "Descrição": desc,
        "Tipo de peça": tipo_peca,
        "Total": total
    }])

    if os.path.exists(hist_path) and os.path.getsize(hist_path) > 0:
        nova_linha.to_csv(hist_path, mode="a", header=False, index=False)
    else:
        nova_linha.to_csv(hist_path, index=False)

# Exibir histórico (sem quebrar se vazio)
st.divider()
st.subheader("📚 Histórico de Peças")

hist_path = "data/historico.csv"
if os.path.exists(hist_path) and os.path.getsize(hist_path) > 0:
    try:
        st.dataframe(pd.read_csv(hist_path), use_container_width=True)
    except pd.errors.EmptyDataError:
        st.info("Ainda não há histórico. Gere o primeiro custo para registrar.")
else:
    st.info("Ainda não há histórico. Gere o primeiro custo para registrar.")
