import pandas as pd
import time
from typing import List
from cnpja_api.cnpja_api import CNPJaAPI



class CNPJaLoteConsulta:
    
    def __init__(self, api: CNPJaAPI, consultas_por_minuto: int = 10):
        self.api = api
        self.consultas_por_minuto = consultas_por_minuto
        self.sleep_time = 60 / self.consultas_por_minuto
        
    @property
    def saldo_consultas(self):
        return self.api.consultar_saldo()

    def consultar_lote(self, cnpjs: List[str], on_progress=None, check_cancel=None) -> List[dict]:
        resultados = []
        cnpjs_unicos = list(set(cnpjs))  # remove duplicados    
        total = len(cnpjs_unicos)

        tempo_primeira_consulta = None

        for i, cnpj in enumerate(cnpjs_unicos):
            try:
                # Consulta CNPJ
                inicio = time.time()
                dados = self.api.consultar_cnpj(cnpj)
                time.sleep(self.sleep_time)  # Respeita o limite configurado
                fim = time.time()
                
                if tempo_primeira_consulta is None:
                    tempo_primeira_consulta = fim - inicio
                
                dados_cnpj = {
                    "REG": "001",
                    "CNPJ": dados.get("taxId"),
                    "Razão Social": dados.get("company", {}).get("name"),
                    "Nome Fantasia": dados.get("alias"),
                    "Data Abertura": dados.get("founded"),
                    "Capital Social": dados.get("company", {}).get("equity"),
                    "Situação Cadastral": dados.get("status", {}).get("text"),
                    "Natureza Jurídica": dados.get("company", {}).get("nature", {}).get("text"),
                    "Porte": dados.get("company", {}).get("size", {}).get("acronym"),
                    "Município": dados.get("address", {}).get("city"),
                    "UF": dados.get("address", {}).get("state"),
                    "CEP": dados.get("address", {}).get("zip"),
                    "Pais": dados.get("address", {}).get("country", {}).get("name")
                }
                resultados.append(dados_cnpj)
                
                resultados.append({
                    "REG": "002",
                    "CNPJ": dados.get("taxId"),
                    "CNAE": dados.get("mainActivity", {}).get("id", ""),
                    "Descricao": dados.get("mainActivity", {}).get("text", ""),
                    "Principal": "Sim"
                })

                for atividade in dados.get("sideActivities", []):
                    resultados.append({
                        "REG": "002",
                        "CNPJ": dados.get("taxId"),
                        "CNAE": atividade.get("id"),
                        "Descricao": atividade.get("text"),
                        "Principal": "Não"
                    })
                
                for socio in dados.get("company", {}).get("members", []):
                    resultados.append({
                        "REG": "003",
                        "CNPJ": dados.get("taxId"),
                        "Nome": socio.get("person", {}).get("name"),
                        "Qualificação": socio.get("role", {}).get("text"),
                        "Idade": socio.get("person", {}).get("age"),
                        "CPF": socio.get("person", {}).get("taxId"),
                    })
                
            except Exception as e:
                resultados.append({"REG": "999", "CNPJ": cnpj, "Falha na consulta": str(e)})
            
            if on_progress:
                if tempo_primeira_consulta:
                    tempo_restante = (total - (i + 1)) * tempo_primeira_consulta
                else:
                    tempo_restante = None
                on_progress(i + 1, total, tempo_restante)
            
            # Se cancelou, adiciona uma linha de log no fim (sem sobrepor resultados)
            if check_cancel and check_cancel():
                resultados.append({"REG": "999", "CNPJ": "", "Erro": "Consulta cancelada pelo usuário."})  
                break      
            
        return resultados

    def exportar_para_excel(self, resultados: List[dict], caminho_arquivo: str) -> None:
        df = pd.DataFrame(resultados)
        with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
            for registro in df["REG"].unique():
                df_relatorio = df[df["REG"] == registro].reset_index(drop=True).dropna(axis=1, how="all").infer_objects(copy=False).fillna("")
                df_relatorio.to_excel(writer, sheet_name=f"REG_{registro}", index=False)
