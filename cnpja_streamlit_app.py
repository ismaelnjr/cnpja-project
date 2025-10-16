import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import pandas as pd
import os
import math
from cnpja_api.cnpja_api import CNPJaAPI
from cnpja_api.cnpja_lote_consulta import CNPJaLoteConsulta

try:
    CNPJA_API_KEY = st.secrets["CNPJA_API_KEY"]
except (StreamlitSecretNotFoundError):
    # Fallback para ambiente local com .env ou variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    CNPJA_API_KEY = os.getenv("CNPJA_API_KEY")

# Validação da chave
if not CNPJA_API_KEY:
    raise ValueError("A chave da API (CNPJA_API_KEY) não foi definida.")

if "cancelar_consulta" not in st.session_state:
    st.session_state.cancelar_consulta = False
if "consulta_em_andamento" not in st.session_state:
    st.session_state.consulta_em_andamento = False
if "resultado" not in st.session_state:
    st.session_state.resultado = None

st.set_page_config(page_title="Consulta CNPJ em Lote", layout="wide")

st.title("🔎 Consulta e Exportação de CNPJs - CNPJa API")

st.markdown("Informe uma lista de CNPJs (um por linha) e clique em **Consultar** para obter os dados da empresa, incluindo CNAEs e dados cadastrais.")

# Campo de texto para entrada de CNPJs
cnpj_input = st.text_area("Lista de CNPJs", height=200, placeholder="Digite ou cole os CNPJs aqui, um por linha...")

# Parâmetro de consultas por minuto via Streamlit secrets/config
try:
    consultas_por_minuto = st.secrets.get("CONSULTAS_POR_MINUTO", 10)
except (StreamlitSecretNotFoundError):
    consultas_por_minuto = 10

exibir_cnae = st.checkbox("Mostrar atividades (CNAEs)", value=True)
exibir_qsa = st.checkbox("Mostrar QSA (Quadro de Sócios e Administradores)", value=True)
exibir_simples = st.checkbox("Verificar Simples Nacional", value=False)

api = CNPJaAPI(CNPJA_API_KEY)  
cliente = CNPJaLoteConsulta(api, consultas_por_minuto=consultas_por_minuto)

# Botão de consulta
if st.button("Consultar CNPJs"):    
    st.session_state.iniciar_consulta = True
    st.session_state.consulta_em_andamento = True
    st.session_state.cancelar_consulta = False
    
if st.session_state.get("iniciar_consulta", False):
    cnpjs = [cnpj.strip() for cnpj in cnpj_input.splitlines() if cnpj.strip()]
    
    if not cnpjs:
        st.warning("⚠️ Informe ao menos um CNPJ válido.")
        st.session_state.iniciar_consulta = False
        st.session_state.consulta_em_andamento = False
    else:
        with st.spinner("Preparando consulta..."):
                        
            progresso = st.progress(0)
            status_text = st.empty()
            
            def verificar_cancelamento():
                return st.session_state.cancelar_consulta
            
            def atualizar_progresso(atual, total, tempo_restante=None):
                progresso.progress(atual / total)
                if tempo_restante:
                    minutos = math.ceil(tempo_restante / 60)
                    status_text.text(f"Consultando {atual} de {total} CNPJs... ⏳ ~{minutos} min restantes")
                else:
                    status_text.text(f"Consultando {atual} de {total} CNPJs...")

            cancelar_placeholder = st.empty()
            def render_cancelar():
                if cancelar_placeholder.button("❌ Cancelar Consulta"):
                    st.session_state.cancelar_consulta = True
            render_cancelar()

            st.session_state.resultado = cliente.consultar_lote(
                cnpjs, 
                on_progress=atualizar_progresso,
                check_cancel=verificar_cancelamento,
                verificar_simples=exibir_simples
            )
            
            # Reseta flags
            st.session_state.iniciar_consulta = False
            st.session_state.consulta_em_andamento = False
            cancelar_placeholder.empty() 
            
            if st.session_state.cancelar_consulta:
                st.warning("Consulta cancelada pelo usuário. Resultados parciais exibidos abaixo.")
            else:
                status_text.text(f"Resultados prontos! Mosntrando CNPJs consultados.")

if st.session_state.resultado:
    with st.spinner("Processando resultado..."):
        # Organiza por REG para exportação e exibição
        df = pd.DataFrame(st.session_state.resultado)
        
        if "001" in df["REG"].values:
            st.subheader("📋 Dados Cadastrais (REG 001)")
            st.dataframe(df[df["REG"] == "001"].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna(""))

        if "002" in df["REG"].values and exibir_cnae:
            st.subheader("🏷️ CNAEs (REG 002)")
            st.dataframe(df[df["REG"] == "002"].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna(""))
            
        if "003" in df["REG"].values and exibir_qsa:
            st.subheader("🧑‍💼 QSA (REG 003)")
            st.dataframe(df[df["REG"] == "003"].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna(""))

        if "900" in df["REG"].values and exibir_simples:
            st.subheader("🏢 Simples Nacional (REG 900)")
            st.dataframe(df[df["REG"] == "900"].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna(""))

        if "999" in df["REG"].values:
            st.subheader("❌ Erros de Consulta (REG 999)")
            st.dataframe(df[df["REG"] == "999"].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna(""))

        # Exportação
        caminho_excel = "exportacao_consulta_cnpjs.xlsx"
        cliente.exportar_para_excel(st.session_state.resultado, caminho_excel)

        with open(caminho_excel, "rb") as f:
            st.download_button(
                label="⬇️ Baixar Resultado em Excel",
                data=f,
                file_name="exportacao_consulta_cnpjs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
