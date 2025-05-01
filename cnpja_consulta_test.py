from cnpja_api.cnpja_api import CNPJaAPI
import json
import os

api = CNPJaAPI(os.getenv("CNPJA_API_KEY"))

cnpj = "01.430.822/0001-75"
filename = f"{cnpj.replace('.', '').replace('/', '').replace('-', '')}_consulta_cnpj.json"

response = api.consultar_cnpj(cnpj)
with open(filename, "w", encoding="utf-8") as f:
    json.dump(response, f, indent=4, ensure_ascii=False)
