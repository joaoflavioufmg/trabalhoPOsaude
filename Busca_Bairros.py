# %%
import pandas as pd
from shapely.geometry import Polygon, Point
import json
from dbfread import DBF
import pyreadstat
import cantools
import requests
from haversine import haversine, Unit

# session = requests.Session()


# Tentiva de encontrar bairro específico por instalação deu errado. Usar método de aproximação!
# def get_neighborhood(lat, lon):
#     url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}54&lon={lon}&zoom=14&addressdetails=1"
#     session.headers.update({'User-Agent': 'MyPythonApp/1.0 (+https://meusite.com)'})
#     response = session.get(url)
#     data = response.json()

#     if response.status_code == 200 and 'address' in data:
#         return data['address'].get('suburb', None) or data['address'].get('neighbourhood', None)
#     return None

# latitude = -19.9437013370475
# longitude = -44.06693487176

# bairro = get_neighborhood(latitude, longitude)
# print(f"Bairro: {bairro}")


# %%
def converte_CD_MUN(x):
    x = str(x)
    return x[: len(x) - 1]


def retorna_UBS(dist, mun, coord_CS, df_merge):
    def func_ord(item):
        return haversine(item[1], coord_CS)

    print(f"Rodando para {mun}")
    # Comparar esse NaN do pandas!
    list_aux = []
    try:
        df_aux = df_merge.loc[df_merge.CO_MUNICIPIO == int(mun)].reset_index()
        for i in set(df_aux.DS_SEGMENTO_ESF):
            try:
                if dist.upper() in i:
                    list_aux.append(i)
            except:
                print(f"{i} deu errado")

        if len(list_aux) > 0:
            df_aux = df_aux.loc[df_aux.DS_SEGMENTO_ESF.isin(list_aux)].reset_index()

        # instalações possíveis:
        coords_inst = {
            int(it): [
                float(list(df_aux.loc[df_aux.cnes == it]["latitude"])[0]),
                float(list(df_aux.loc[df_aux.cnes == it]["longitude"])[0]),
            ]
            for it in list(pd.unique(df_aux.cnes))
        }
        sorted_dict = dict(sorted(coords_inst.items(), key=func_ord))
        return list(sorted_dict.keys())[0]
    except:
        return "avaliar separadamente"


# %%
path_coords_ins = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\Dados Instalacoes existestes\dados_instalacoes_reais_com_coords.csv"
path_CS = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\dados_PRONTOS_para_modelo_OTM\dados_cidades_full_MG.xlsx"


# path_relacao_UBS_bairro = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\Dados Instalacoes existestes\BASE_DE_DADOS_CNES_202411\bases_uteis\Relacao_bairro_UBS.csv"
path_ex = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\Dados Instalacoes existestes\BASE_DE_DADOS_CNES_202411\bases_uteis\Relacao_bairro_UBS_v2.xlsx"

df_ins = pd.read_csv(path_coords_ins, sep=",")
df_cs = pd.read_excel(path_CS)
df_rl = pd.read_excel(path_ex)

# %%
estado = "MG"
df_ins = df_ins.loc[df_ins.uf_sigla == "MG"]
df_ins_merge = (
    df_ins[["cnes", "latitude", "longitude"]].reset_index().drop("index", axis=1)
)

df_merge = df_rl.merge(df_ins_merge, left_on="CO_CNES_ESF", right_on="cnes")
df_cs["mun_convert"] = df_cs.CD_MUN.apply(lambda x: converte_CD_MUN(x))
df_merge = df_merge.loc[df_merge.latitude != "Avaliar Coordenada separado"]
# df_cs = df_cs.loc[df_cs.NM_MUN == "Contagem"]
# %%
df_cs["UBS_ref"] = df_cs.apply(
    lambda x: retorna_UBS(
        x.NM_SUBDIST, x.mun_convert, [x.Latitude, x.Longitude], df_merge
    ),
    axis=1,
)


df_end = df_cs[
    [
        "CD_SETOR",
        "NM_MUN",
        "Total de pessoas",
        "coordinates",
        "CD_CONCURB",
        "NM_SUBDIST",
        "ponto_central",
        "Latitude",
        "Longitude",
        "mun_convert",
        "UBS_ref",
    ]
]

df_end.to_excel("dados_populacao_com_UBS.xlsx")
