import pandas as pd
from typing import List
from cnpja_api.cnpja_api import CNPJaAPI


class CNPJaLoteConsulta:
    def __init__(self, api: CNPJaAPI):
        self.api = api

    def consultar_lote(self, cnpjs: List[str]) -> List[dict]:
        resultados = []
        for cnpj in cnpjs:
            try:
                dados = self.api.consultar_cnpj(cnpj)
                dados_cnpj = {
                    "REG": "001",
                    "CNPJ": dados.get("taxId"),
                    "Razão Social": dados.get("company", {}).get("name"),
                    "Nome Fantasia": dados.get("alias"),
                    "Situação Cadastral": dados.get("status", {}).get("text"),
                    "Natureza Jurídica": dados.get("company", {}).get("nature", {}).get("text"),
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
                    "Principal": True
                })

                for atividade in dados.get("secondaryActivities", []):
                    resultados.append({
                        "REG": "002",
                        "CNPJ": dados.get("taxId"),
                        "CNAE": atividade.get("id"),
                        "Descricao": atividade.get("text"),
                        "Principal": False
                    })
                
            except Exception as e:
                resultados.append({"REG": "999", "CNPJ": cnpj, "Erro": str(e)})
        return resultados

    def exportar_para_excel(self, resultados: List[dict], caminho_arquivo: str) -> None:
        df = pd.DataFrame(resultados)
        with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
            if "001" in df["REG"].values:
                df_001 = df[df["REG"] == "001"]
                colunas_001 = ["REG", "CNPJ", "Razão Social", "Nome Fantasia", "Situação Cadastral",
                               "Natureza Jurídica", "Município", "UF", "CEP", "Pais"]
                df_001[colunas_001].to_excel(writer, sheet_name="REG_001", index=False)

            if "002" in df["REG"].values:
                df_002 = df[df["REG"] == "002"]
                colunas_002 = ["REG", "CNPJ", "CNAE", "Descricao", "Principal"]
                df_002[colunas_002].to_excel(writer, sheet_name="REG_002", index=False)

            if "999" in df["REG"].values:
                df_999 = df[df["REG"] == "999"]
                df_999.to_excel(writer, sheet_name="REG_999", index=False)
