import os
from cnpja_api.cnpja_api import CNPJaAPI
from cnpja_api.cnpja_lote_consulta import CNPJaLoteConsulta

if __name__ == "__main__":
    api = CNPJaAPI(os.getenv("CNPJA_API_KEY"))
    lote_consulta = CNPJaLoteConsulta(api)

    cnpjs = ["27.865.757/0001-02", "40.432.544/0001-47"]
    resultado = lote_consulta.consultar_lote(cnpjs)
    lote_consulta.exportar_para_excel(resultado, "exportacao.xlsx")