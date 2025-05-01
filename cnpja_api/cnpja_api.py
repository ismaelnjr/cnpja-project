import os
import requests

class CNPJaAPI:
    BASE_URL = "https://api.cnpja.com"

    def __init__(self, api_key: str = None):
        
        if api_key:
            self.api_key = api_key
        elif os.getenv("CNPJA_API_KEY"):
            self.api_key = os.getenv("CNPJA_API_KEY")
        else:
            raise ValueError("A chave da API (CNPJA_API_KEY) não foi definida.")

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

    def consultar_cnpj(self, cnpj: str) -> dict:
        cnpj = self._normalize_taxid(cnpj)
        url = f"{self.BASE_URL}/office/{cnpj}"
        return self._get(url)

    def consultar_empresa_por_nome(self, nomes: list[str]) -> dict:
        query = ",".join(nomes)
        url = f"{self.BASE_URL}/office?company.name.in={query}"
        return self._get(url)

    def consultar_cpf(self, cpfs: list[str]) -> dict:
        query = ",".join(cpfs)
        url = f"{self.BASE_URL}/person?taxId.in={query}"
        return self._get(url)

    def consultar_rfb(self, cnpj: str) -> dict:
        cnpj = self._normalize_taxid(cnpj)
        url = f"{self.BASE_URL}/rfb?taxId={cnpj}"
        return self._get(url)

    def consultar_simples(self, cnpj: str) -> dict:
        cnpj = self._normalize_taxid(cnpj)
        url = f"{self.BASE_URL}/simples?taxId={cnpj}"
        return self._get(url)

    def consultar_saldo(self) -> dict:
        url = f"{self.BASE_URL}/credit"
        return self._get(url)

    def _get(self, url: str) -> dict:
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erro {response.status_code}: {response.text}")

    def _normalize_taxid(self, taxid: str) -> str:
        return taxid.replace(".", "").replace("/", "").replace("-", "").strip()
