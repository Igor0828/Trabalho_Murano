import streamlit as st
import pandas as pd
import os
import hashlib
from utils.calculo import calcular_custo_total, calcular_parcela
from utils.excel import gerar_excel

# -------------------------------
# 🔐 PROTEÇÃO POR SENHA
# -------------------------------
def check_password():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Sistema Interno")
        st.subheader("Acesso restrito")

        senha = st.text_input("Digite a senha", type="password")

        if st.button("Entrar"):
            if hashlib.sha256(senha.encode()).hexdigest() == "123456":
                st.session_state.autenticado = True
                st.experimental_rerun()
            else:
                st.error("Senha incorreta")

        st.stop()

check_password()

# -------------------------------
# 🧵 APP PRINCIPAL
# -------------------------------
st.set_page_config("Custo Peça Piloto", layout="centered")
st.title("🧵 Sistema de Custo – Peça Piloto")

# --- Preços fixos ---
st.sidebar.title("💰 Preços Fixos")
aviamentos = st.sidebar.number_input("Aviamentos", 0.0, value=10.8)
linha = st.sidebar.number_input("Linha", 0.0, value=2.4)
lavanderia = st.sidebar.number_input("Lavanderia", 0.0, value=18.0)
mao_obra = st.sidebar.number_input("Mão de obra", 0.0, value=28.0)
acabamento = st.sidebar.number_input("Acabamento", 0.0, value=6.5)
indiretos = st.sidebar.number_input("Custos indiretos", 0.0, value=15.0)

# --- Formulário ---
with st.form("form"):
    st.subheader("Identificação da Peça")
    ref = st.text_input("Referência")
    desc = st.text_input("Descrição")
    tecido_tipo = st.selectbox("Tipo de tecido", ["Jeans", "Sarja"])
    cor = st.text_input("Cor / Lavagem")
    tamanho = st.text_input("Tamanho piloto")

    st.subheader("Custo variável")
    tecido_valor = st.number_input("Tecido (R$)", 0.0)

    parcelas = st.number_input("Parcelas", 1, 12, 1)
    imagem = st.file_uploader("Imagem da peça piloto", ["jpg", "png"])

    submit = st.form_submit_button("Gerar custo")

# --- Processamento ---
if submit:
    custos = {
        "Tecido": tecido_valor,
        "Aviamentos": aviamentos,
        "Linha": linha,
        "Lavanderia": lavanderia,
        "Mão de obra": mao_obra,
        "Acabamento": acabamento,
        "Indiretos": indiretos
    }

    total = calcular_custo_total(custos)
    valor_parcela = calcular_parcela(total, parcelas)

    st.success(f"Custo total: R$ {total:.2f}")
    st.info(f"{parcelas}x de R$ {valor_parcela:.2f}")

    if imagem:
        st.image(imagem, width=300)

    dados_peca = {
        "Referência": ref,
        "Descrição": desc,
        "Tecido": tecido_tipo,
        "Cor/Lavagem": cor,
        "Tamanho": tamanho
    }

    excel = gerar_excel(dados_peca, custos, total, parcelas, valor_parcela)

    st.download_button(
        "📥 Baixar Excel",
        excel.getvalue(),
        "custo_peca_piloto.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Histórico ---
    os.makedirs("data", exist_ok=True)
    hist = pd.DataFrame([{
        "Referência": ref,
        "Descrição": desc,
        "Total": total
    }])

    path = "data/historico.csv"
    if os.path.exists(path):
        hist.to_csv(path, mode="a", header=False, index=False)
    else:
        hist.to_csv(path, index=False)

# --- Histórico ---
if os.path.exists("data/historico.csv"):
    st.subheader("📚 Histórico de Peças")
    st.dataframe(pd.read_csv("data/historico.csv"))
