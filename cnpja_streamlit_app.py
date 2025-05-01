import streamlit as st
import pandas as pd
from cnpja_api.cnpja_api import CNPJaAPI
from cnpja_api.cnpja_lote_consulta import CNPJaLoteConsulta

st.set_page_config(page_title="Consulta CNPJ em Lote", layout="wide")

st.title("🔎 Consulta e Exportação de CNPJs - CNPJa API")

st.markdown("Informe uma lista de CNPJs (um por linha) e clique em **Consultar** para obter os dados da empresa, incluindo CNAEs e dados cadastrais.")

# Campo de texto para entrada de CNPJs
cnpj_input = st.text_area("Lista de CNPJs", height=200, placeholder="Digite ou cole os CNPJs aqui, um por linha...")

# Botão de consulta
if st.button("Consultar CNPJs"):
    cnpjs = [cnpj.strip() for cnpj in cnpj_input.splitlines() if cnpj.strip()]
    
    if not cnpjs:
        st.warning("⚠️ Informe ao menos um CNPJ válido.")
    else:
        with st.spinner("Consultando CNPJs..."):
            api = CNPJaAPI()  # Usa chave do .env
            cliente = CNPJaLoteConsulta(api)
            resultado = cliente.consultar_lote(cnpjs)

            # Organiza por REG para exportação e exibição
            df = pd.DataFrame(resultado)
            
            if "001" in df["REG"].values:
                st.subheader("📋 Dados Cadastrais (REG 001)")
                st.dataframe(df[df["REG"] == "001"].reset_index(drop=True).dropna(axis=1, how="all"))

            if "002" in df["REG"].values:
                st.subheader("🏷️ CNAEs (REG 002)")
                st.dataframe(df[df["REG"] == "002"].reset_index(drop=True).dropna(axis=1, how="all"))

            if "999" in df["REG"].values:
                st.subheader("❌ Erros de Consulta (REG 999)")
                st.dataframe(df[df["REG"] == "999"].reset_index(drop=True).dropna(axis=1, how="all"))

            # Exportação
            caminho_excel = "exportacao_consulta_cnpjs.xlsx"
            cliente.exportar_para_excel(resultado, caminho_excel)

            with open(caminho_excel, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar Resultado em Excel",
                    data=f,
                    file_name="exportacao_consulta_cnpjs.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
