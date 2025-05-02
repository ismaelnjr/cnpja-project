from cnpja_api.cnpja_api import CNPJaAPI
import os

api = CNPJaAPI(os.getenv("CNPJA_API_KEY"))

response = api.consultar_saldo()
print(response)