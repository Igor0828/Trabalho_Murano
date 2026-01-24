import streamlit as st
import pandas as pd
import os
from pathlib import Path

from utils.calculo import calcular_custo_total
from utils.excel import gerar_excel

# ✅ sempre no topo antes de qualquer st.title/st.write
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


check_password()

st.title("🧵 Sistema de Custo – Peça Piloto")


# -------------------------------
# 📌 Leitura de tabelas (Oficina / Lavanderia)
# -------------------------------
@st.cache_data
def carregar_tabela_csv(path_str: str):
    path = Path(path_str)
    if not path.exists():
        return None

    df = pd.read_csv(path)
    # Normaliza colunas esperadas
    for col in ["valor_min", "valor_max"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if "servico" not in df.columns:
        df["servico"] = ""

    if "nota_ziad" not in df.columns:
        df["nota_ziad"] = ""

    df["servico"] = df["servico"].astype(str)
    df["nota_ziad"] = df["nota_ziad"].fillna("").astype(str)

    return df


df_oficina = carregar_tabela_csv("data/oficina.csv")
df_lavanderia = carregar_tabela_csv("data/lavanderia.csv")

# Estados
if "oficina_itens" not in st.session_state:
    st.session_state.oficina_itens = []

if "lavanderia_itens" not in st.session_state:
    st.session_state.lavanderia_itens = []

if "adicionais_itens" not in st.session_state:
    # 5 mais usados, estilo blocos
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
# 🧵 Tecido (R$/m + consumo)
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
    tecido_valor = tecido_preco_m * tecido_consumo_m
    st.metric("Custo do tecido (R$)", f"R$ {tecido_valor:.2f}")


# -------------------------------
# 💰 Custos base (presets)
# -------------------------------
st.subheader("💰 Custos base")

col1, col2, col3 = st.columns(3)
with col1:
    aviamentos = st.number_input("Aviamentos (R$)", min_value=0.0, value=3.80, step=0.10)
    linha = st.number_input("Linha (R$)", min_value=0.0, value=2.40, step=0.10)

with col2:
    acabamento = st.number_input("Acabamento (R$)", min_value=0.0, value=6.50, step=0.10)

with col3:
    despesa_fixa = st.number_input("Despesa fixa (R$)", min_value=0.0, value=5.50, step=0.10)


# -------------------------------
# 🏭 Oficina (somar serviços, sem repetir)
# -------------------------------
st.subheader("🏭 Oficina (serviços)")

def ui_somar_servicos(df: pd.DataFrame, state_key: str, titulo_total: str, prefix: str):
    if df is None:
        st.warning(f"Tabela não encontrada: data/{prefix}.csv")
        return 0.0, 0.0, 0.0  # tabela_min, tabela_max, real

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
        add = st.button("Adicionar", use_container_width=True, key=f"{prefix}_add_btn")

    if add and escolhido != "(selecione)":
        linha_df = df[df["servico"] == escolhido].iloc[0].to_dict()
        valor_sugerido = float(linha_df.get("valor_min", 0.0))  # faixa começa no mínimo

        itens.append({
            "servico": str(linha_df.get("servico", "")),
            "valor_min": float(linha_df.get("valor_min", 0.0)),
            "valor_max": float(linha_df.get("valor_max", float(linha_df.get("valor_min", 0.0)))),
            "nota_ziad": str(linha_df.get("nota_ziad", "")),
            "valor_real": valor_sugerido
        })
        st.session_state[state_key] = itens
        st.rerun()

    if itens:
        st.markdown("### Serviços adicionados")

        total_min = 0.0
        total_max = 0.0
        total_real = 0.0

        for idx, item in enumerate(itens):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])

                with c1:
                    st.write(f"**{item['servico']}**")
                    if item.get("nota_ziad"):
                        st.caption(f"🟥 Nota: {item['nota_ziad']}")

                    if float(item["valor_min"]) != float(item["valor_max"]):
                        st.caption(f"Tabela: R$ {item['valor_min']:.2f} – R$ {item['valor_max']:.2f}")
                    else:
                        st.caption(f"Tabela: R$ {item['valor_min']:.2f}")

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

            total_min += float(item["valor_min"])
            total_max += float(item["valor_max"])
            total_real += float(item["valor_real"])

        st.markdown(f"### Totais — {titulo_total}")
        t1, t2, t3 = st.columns(3)
        t1.metric("Tabela (mín)", f"R$ {total_min:.2f}")
        t2.metric("Tabela (máx)", f"R$ {total_max:.2f}")
        t3.metric("Real", f"R$ {total_real:.2f}")

        st.session_state[state_key] = itens
        return total_min, total_max, total_real

    st.info("Adicione serviços para compor o custo.")
    return 0.0, 0.0, 0.0


of_min, of_max, total_oficina_real = ui_somar_servicos(df_oficina, "oficina_itens", "Oficina", "oficina")


# -------------------------------
# 🧼 Lavanderia (igual oficina)
# -------------------------------
st.subheader("🧼 Lavanderia (serviços)")

lav_min, lav_max, total_lavanderia_real = ui_somar_servicos(df_lavanderia, "lavanderia_itens", "Lavanderia", "lavanderia")


# -------------------------------
# ➕ Adicionais (dinâmicos em blocos, sem repetir)
# -------------------------------
st.subheader("➕ Adicionais (valores manuais)")

col_add1, col_add2, col_add3 = st.columns([2.2, 1.2, 1])
with col_add1:
    novo_nome = st.text_input("Nome do adicional", placeholder="Ex: Zíper, Etiqueta, Botão extra...", key="add_nome")
with col_add2:
    novo_valor = st.number_input("Valor (R$)", min_value=0.0, value=0.0, step=0.10, key="add_valor")
with col_add3:
    add_novo = st.button("Adicionar", use_container_width=True, key="add_btn")

nomes_existentes = {i["nome"].strip().lower() for i in st.session_state.adicionais_itens}

if add_novo:
    nome_limpo = (novo_nome or "").strip()
    if not nome_limpo:
        st.warning("Digite um nome para o adicional.")
    elif nome_limpo.lower() in nomes_existentes:
        st.warning("Esse adicional já existe. Ajuste o valor no bloco abaixo.")
    else:
        st.session_state.adicionais_itens.append({"nome": nome_limpo, "valor": float(novo_valor)})
        st.rerun()

st.markdown("### Itens")
cols = st.columns(3)

for idx, item in enumerate(st.session_state.adicionais_itens):
    col = cols[idx % 3]
    with col:
        with st.container(border=True):
            st.write(f"**{item['nome']}**")
            val = st.number_input(
                "R$",
                min_value=0.0,
                value=float(item["valor"]),
                step=0.10,
                key=f"ad_val_{idx}",
                label_visibility="collapsed",
            )
            st.session_state.adicionais_itens[idx]["valor"] = float(val)

            # Remove apenas os adicionados depois (os 5 primeiros ficam)
            if idx >= 5:
                if st.button("Remover", key=f"ad_rem_{idx}", use_container_width=True):
                    st.session_state.adicionais_itens.pop(idx)
                    st.rerun()

total_adicionais = sum(i["valor"] for i in st.session_state.adicionais_itens)
st.metric("Total de adicionais (R$)", f"R$ {total_adicionais:.2f}")

# Exporta só >0
adicionais = {i["nome"]: i["valor"] for i in st.session_state.adicionais_itens if i["valor"] > 0}


# -------------------------------
# ✅ Gerar custo + Excel
# -------------------------------
st.divider()
gerar = st.button("✅ Gerar custo e Excel", type="primary", use_container_width=True)

if gerar:
    custos = {
        "Tecido": tecido_valor,
        "Aviamentos": aviamentos,
        "Linha": linha,
        "Acabamento": acabamento,
        "Despesa fixa": despesa_fixa,
        "Oficina (real)": total_oficina_real,
        "Lavanderia (real)": total_lavanderia_real,
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
        "Cor/Lavagem": cor_lavagem,
        "Tecido (nome)": tecido_nome,
        "Tecido (tipo)": tecido_tipo,
        "Preço tecido (R$/m)": tecido_preco_m,
        "Consumo (m)": tecido_consumo_m,
    }

    excel_buffer = gerar_excel(
        dados_peca=dados_peca,
        custos=custos,
        total=total,
        oficina_itens=st.session_state.oficina_itens,
        lavanderia_itens=st.session_state.lavanderia_itens,
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


# -------------------------------
# 📚 Exibir histórico (sem quebrar)
# -------------------------------
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
