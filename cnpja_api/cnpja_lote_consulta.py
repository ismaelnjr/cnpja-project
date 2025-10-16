import pandas as pd
import time
from typing import List
from datetime import datetime
from cnpja_api.cnpja_api import CNPJaAPI



class CNPJaLoteConsulta:
    
    def __init__(self, api: CNPJaAPI, consultas_por_minuto: int = 10):
        self.api = api
        self.consultas_por_minuto = consultas_por_minuto
        self.sleep_time = 60 / self.consultas_por_minuto
    
    def _formatar_data(self, data_str: str) -> str:
        """
        Formata uma data para o formato brasileiro dd/mm/yyyy
        Aceita formatos: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS.000Z
        """
        if not data_str or data_str == "None":
            return ""
        
        try:
            # Remove informações de timezone se presentes
            data_limpa = data_str.split('T')[0] if 'T' in data_str else data_str
            
            # Tenta parsear a data
            if len(data_limpa) == 10 and data_limpa.count('-') == 2:
                # Formato YYYY-MM-DD
                data_obj = datetime.strptime(data_limpa, '%Y-%m-%d')
                return data_obj.strftime('%d/%m/%Y')
            else:
                # Se não conseguir parsear, retorna a string original
                return data_str
        except (ValueError, AttributeError):
            # Se houver erro na formatação, retorna a string original
            return data_str
        
    @property
    def saldo_consultas(self):
        return self.api.consultar_saldo()

    def consultar_lote(self, cnpjs: List[str], on_progress=None, check_cancel=None, verificar_simples=False, verificar_contribuintes=False) -> List[dict]:
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
                    "Data Abertura": self._formatar_data(dados.get("founded")),
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
                
                # Consulta Simples Nacional se solicitado
                if verificar_simples:
                    try:
                        dados_simples = self.api.consultar_simples(cnpj)
                        if dados_simples:
                            simples_data = dados_simples.get("simples", {})
                            simei_data = dados_simples.get("simei", {})
                            
                            is_simples = simples_data.get("optant", False)
                            is_simei = simei_data.get("optant", False)
                            
                            resultados.append({
                                "REG": "900",
                                "CNPJ": dados.get("taxId"),
                                "Simples Nacional": "Sim" if is_simples else "Não",
                                "Data Opção Simples": self._formatar_data(simples_data.get("since", "")),
                                "SIMEI": "Sim" if is_simei else "Não",
                                "Data Opção SIMEI": self._formatar_data(simei_data.get("since", "")),
                                "Última Atualização": self._formatar_data(dados_simples.get("updated", ""))
                            })
                        else:
                            resultados.append({
                                "REG": "900",
                                "CNPJ": dados.get("taxId"),
                                "Simples Nacional": "Dados não disponíveis",
                                "Data Opção Simples": "",
                                "SIMEI": "",
                                "Data Opção SIMEI": "",
                                "Última Atualização": ""
                            })
                    except Exception as e:
                        resultados.append({
                            "REG": "900",
                            "CNPJ": dados.get("taxId"),
                            "Simples Nacional": "Erro na consulta",
                            "Erro": str(e)
                        })
                
                # Consulta Cadastro de Contribuintes se solicitado
                if verificar_contribuintes:
                    try:
                        # Lista de estados brasileiros para consultar inscrições
                        estados_brasil = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
                                         'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
                                         'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
                        dados_contribuintes = self.api.consultar_cadastro_contribuintes(cnpj, registrations=estados_brasil)
                        if dados_contribuintes and dados_contribuintes.get("registrations"):
                            for registro in dados_contribuintes.get("registrations", []):
                                resultados.append({
                                    "REG": "800",
                                    "CNPJ": dados.get("taxId"),
                                    "Estado": registro.get("state", ""),
                                    "Número Inscrição": registro.get("number", ""),
                                    "Status": registro.get("status", {}).get("text", ""),
                                    "Tipo": registro.get("type", {}).get("text", ""),
                                    "Ativo": "Sim" if registro.get("enabled", False) else "Não",
                                    "Data Status": self._formatar_data(registro.get("statusDate", ""))
                                })
                        else:
                            resultados.append({
                                "REG": "800",
                                "CNPJ": dados.get("taxId"),
                                "Estado": "",
                                "Número Inscrição": "",
                                "Status": "Nenhuma inscrição encontrada",
                                "Tipo": "",
                                "Ativo": "",
                                "Data Status": ""
                            })
                    except Exception as e:
                        resultados.append({
                            "REG": "800",
                            "CNPJ": dados.get("taxId"),
                            "Estado": "",
                            "Número Inscrição": "",
                            "Status": "Erro na consulta",
                            "Tipo": "",
                            "Ativo": "",
                            "Data Status": "",
                            "Erro": str(e)
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
