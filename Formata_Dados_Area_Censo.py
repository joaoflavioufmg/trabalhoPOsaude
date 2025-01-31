"""
# %% """

import pandas as pd
from shapely.geometry import Polygon, Point
import json
import matplotlib.pyplot as plt
import numpy as np


def converte_dados_em_par_coords(x: str):
    coords = x[9:]
    coords = coords.split(",")
    dados_fim = list()
    for par_coords in coords:
        # teste 1: primeiro latitude e depois longitude !
        pr = par_coords.split(" ")
        if len(pr) == 2:
            dados_fim.append((float(pr[1]), float(pr[0])))
        elif len(pr) == 3:
            pr[1] = pr[1].replace("(", "") if "(" in pr[1] else pr[1]
            pr[2] = pr[2].replace(")", "") if ")" in pr[2] else pr[2]
            dados_fim.append((float(pr[2]), float(pr[1])))
    return dados_fim


def calcula_coordenada_centro(pol, retorna_poligono=False):
    if len(pol) == 1:
        polygon = Polygon(pol[0])
    else:
        polygon = Polygon(pol)

    centroid = polygon.centroid
    if retorna_poligono:
        return polygon
    return [centroid.x, centroid.y]  # Latitude e longitude!!!


def classifica_instalacoes(tp):
    # Transformar isso em self quando criar a classe!!
    primaria = ["02 CENTRO DE SAUDE/UNIDADE BASICA"]
    secundaria = ["36 CLINICA/CENTRO DE ESPECIALIDADE"]
    terciaria = ["05 HOSPITAL GERAL", "62 HOSPITAL/DIA - ISOLADO"]
    UPAS = ["04 POLICLINICA", "73 PRONTO ATENDIMENTO"]

    if tp in primaria:
        return "primario"
    if tp in secundaria:
        return "secundario"
    if tp in terciaria:
        return "terceiario"
    if tp in UPAS:
        return "Pronto-atendimento"
    else:
        return "Reclassificar"


def _localiza_celula_censo(
    ponto,
    municipio=None,
    df_censos=None,
    retorna_latitude=False,
    retorna_longitude=False,
):
    try:
        p = ponto[7:]
        pos_espaco = p.find(" ")
        p1 = float(p[:pos_espaco])
        p2_aux = p[pos_espaco:]
        p_par = p2_aux.find(")")
        p2 = float(p2_aux[1:p_par])
        pt = Point(p1, p2)
        if retorna_latitude:
            return p2
        if retorna_longitude:
            return p1
    except:
        return "Avaliar Coordenada separado"
    try:
        df_censos = df_censos.reset_index()
        pos_l = next(
            i
            for i in range(len(df_censos.Obj_Poly))
            if df_censos.Obj_Poly[i].contains(pt)
        )
        print(f"Municipio: {municipio}")
        return df_censos.CD_SETOR[pos_l]
    except:
        return "Não encontrou Local"


# %% Tentativa com dados de todos os municipios baixados do IBGE!!
path_df_censo = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\dados_setor_censitario\Total_Populacao_Censo_v2.csv"
path_df_estratificada = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\dados_setor_censitario\Agregados_por_setores_demografia_BR_v2.xlsx"
path_dict_legenda = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\dados_setor_censitario\dicionario_de_dados_agregados_por_setores_censitarios_v2.xlsx"
path_coords_setores = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\dados_setor_censitario\MG_Malha_Preliminar_2022.json"
with open(path_coords_setores, "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

lt = [
    dados["features"][i]["properties"] | dados["features"][i]["geometry"]
    for i in range(len(dados["features"]))
]

df_full = pd.DataFrame(lt)
df_full["ponto_central"] = df_full.apply(
    lambda x: calcula_coordenada_centro(pol=x.coordinates[0]), axis=1
)
# Divindo em lat e long pra ficar mais facil o tratamento no julia!!
df_full["Latitude"] = df_full.apply(lambda x: x.ponto_central[1], axis=1)
df_full["Longitude"] = df_full.apply(lambda x: x.ponto_central[0], axis=1)

abas_df_legendas = [
    "Dicionário Básico",  # Dados da quantidade de pessoas
    "Dicionário não PCT",
]  # Dados extratifcados por cor ou raça!

# Inicialmente tratarei apenas do dicionário básico, mas para estudos mais profundos da população de cada cédula de censo usar o dicionário não PCT
df_legenda_dados = pd.read_excel(path_dict_legenda, sheet_name="Dicionário Básico")

dict_legenda = dict()
for index, row in df_legenda_dados.iterrows():
    v = row["Variável"].lower()
    dict_legenda[v] = row[
        "Descrição"
    ]  # conversão da relação entre tipo de variável e coluna!!

cols_traduzidas = [v for v in dict_legenda.keys()]
df_full.rename(
    columns={
        col: dict_legenda[col]
        for col in list(df_full.columns)
        if col in cols_traduzidas
    },
    inplace=True,
)
# df_full.to_excel("dados_cidades_full_MG.xlsx")


# %%
# Tratando dados das instalações municipais!
path_dados_instalacoes_saude = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\Dados Instalacoes existestes\CNES _ EXTRATO DAS INSTALAÇÕES FÍSICAS 2.csv"
df_ins = pd.read_csv(path_dados_instalacoes_saude, sep=",")
df_ins["latitude"] = df_ins.apply(
    lambda x: _localiza_celula_censo(x.location, retorna_latitude=True), axis=1
)
df_ins["longitude"] = df_ins.apply(
    lambda x: _localiza_celula_censo(x.location, retorna_longitude=True), axis=1
)

# Filtro das instalações apenas se tem convênio SUS!

# df_ins['classificacao_OTM'] = df_ins.apply(lambda x: classifica_instalacoes(x.tipo_estabelecimento), axis=1)
# ATEÇÃO: CHECAR ESSE FILTRO! 'SEM FINS LUCRATIVOS' por conta do hospital de contagem!
# df_ins = df_ins.loc[
#     (
#         (df_ins.natureza_juridica_tipo == "PÚBLICO")
#         | (df_ins.natureza_juridica_tipo == "SEM FINS LUCRATIVOS")
#     )
# ]


df_ins = df_ins.loc[df_ins.status_estabelecimento == "ATIVO"]
df_ins = df_ins.loc[df_ins.convenio_sus == "SIM"]
df_ins["qt_instalacao_leitos"] = df_ins.apply(
    lambda x: x.qt_instalacao_leitos if isinstance(x.qt_instalacao_leitos, int) else 0,
    axis=1,
)


# localizando em qual CC está cada ponto de saúde!
# %%
"""
filtro coluna tipo_novo_estabelecimento:
UBS: '001 UNIDADE BASICA DE SAUDE', '012 UNIDADE DE ATENCAO DOMICILIAR'
instalação nome: '15 CLINICAS BASICAS' - Tem outras (odontologia, sala curativos, etc) avaliar em conjunto o que considerar!
gestao = MUNICIPAL
natureza_juridica = apenas municipal

OBS: VER UPAS QUE ATENDEM UNIDADE BÁSICA (INSTALAÇÃO NOME!)

"""

df_primary = df_ins.loc[
    (df_ins.tipo_novo_estabelecimento == "001 UNIDADE BASICA DE SAUDE")
]

df_primary = df_ins.loc[
    (
        (df_ins.tipo_novo_estabelecimento == "001 UNIDADE BASICA DE SAUDE")
        | (df_ins.tipo_novo_estabelecimento == "012 UNIDADE DE ATENCAO DOMICILIAR")
    )
]
# df_primary = df_primary.loc[df_primary.instalacao_nome == "15 CLINICAS BASICAS"]


"""
Filtro das secundárias:
UPAs com função secundária, policlinas, centro de especialidade médicas, centros médicos, CM CAE
Filtro do tipo_novo_estabelecimento!

['008 PRONTO ATENDIMENTO', '007 CENTRO DE ASSISTENCIA OBSTETRICA E NEONATAL NORMAL', '018 UNIDADE DE APOIO DIAGNOSTICO'
'022 LABORATORIO DE SAUDE PUBLICA', '010 UNIDADE DE ATENCAO HEMATOLOGICA E/OU HEMOTERAPICA', '015 UNIDADE DE REABILITACAO']

Será necessário filtrar as unidades de pronto atendimento com serviços de nivel 2


Instalações nomes das UPAS que vão ser consideradas secundárias
['16 CLINICAS ESPECIALIZADAS', '15 CLINICAS BASICAS', '18 OUTROS CONSULTORIOS NAO MEDICOS']


"""
lista_tipo_estabelecimento = [
    "04 POLICLINICA",
    "73 PRONTO ATENDIMENTO",
]
lista_servicos_secundarios_UPA = [
    "16 CLINICAS ESPECIALIZADAS",
    "15 CLINICAS BASICAS",
    "18 OUTROS CONSULTORIOS NAO MEDICOS",
]
lista_servicos_secundarios_gerais = [
    "007 CENTRO DE ASSISTENCIA OBSTETRICA E NEONATAL NORMAL",
    "018 UNIDADE DE APOIO DIAGNOSTICO" "022 LABORATORIO DE SAUDE PUBLICA",
    "010 UNIDADE DE ATENCAO HEMATOLOGICA E/OU HEMOTERAPICA",
    "015 UNIDADE DE REABILITACAO",
]


df_secundary = df_ins.loc[df_ins.tipo_estabelecimento.isin(lista_tipo_estabelecimento)]

# %%
leitos_max_HPP = 30
df_hospitais = df_ins.loc[df_ins.tipo_novo_estabelecimento == "006 HOSPITAL"]

#
df_hospitais_tercearios = df_hospitais.drop_duplicates(subset=["nome_fantasia"])
# vou considerar que o total de leitos precisa ser menor que 30!


df_secundary = df_secundary.drop_duplicates(subset=["cnes"])
df_primary = df_primary.drop_duplicates(subset=["cnes"])

# %%
path_equipes = r"C:\Users\marce\OneDrive\Área de Trabalho\Dados PO Saude\Dados Instalacoes existestes\CNES - EXTRATO PROFISSIONAIS SUS_v2.csv"
# df_equipes = pd.read_excel(path_equipes)
df_equipes = pd.read_csv(path_equipes, sep=",")
df_equipes = df_equipes.loc[df_equipes.profissional_atende_sus == "SIM"]
df_equipes.profissional_cbo = df_equipes.profissional_cbo.apply(
    lambda x: x[x.find("-") + 2 :]
)
df_equipes["carga_horaria"] = (
    df_equipes.carga_horaria_hospitalar_sus + df_equipes.carga_horaria_ambulatorial_sus
)
# %%

df_eq_primary = df_equipes.loc[df_equipes.cnes.isin(df_primary.cnes)].reset_index(
    drop=True
)


df_eq_sec = df_equipes.loc[df_equipes.cnes.isin(df_secundary.cnes)].reset_index(
    drop=True
)

df_eq_ter_aux = df_equipes.loc[
    df_equipes.cnes.isin(df_hospitais_tercearios.cnes)
].reset_index(drop=True)


# %%
def retorna_pareto_por_municipio(
    df_full, municipio, percent=0.8, plota=True, param_hora=170, primario=False
):
    df = df_full.loc[df_full.municipio == municipio.upper()]
    if not primario:
        profissoes_chave = [
            "MEDICO",
            "ENFERMEIRO",
            "AUXILIAR DE ENFERMAGEM",
            "NUTRICIONISTA",
            "PSICOLOGO CLINICO",
        ]

    else:
        profissoes_chave = [
            "MEDICO",
            "ENFERMEIRO",
            "AUXILIAR DE ENFERMAGEM",
            "NUTRICIONISTA",
            "PSICOLOGO CLINICO",
            "AGENTE",
            "FONOAUDIOLO",
            "DENTISTA",
            "BUCAL",
            "FARMACEUTICO",
        ]

    lista_cbo_full = [
        i
        for i in pd.unique(df["profissional_cbo"])
        if len([pr for pr in profissoes_chave if pr in i]) > 0
    ]
    df_aux = df.loc[df["profissional_cbo"].isin(lista_cbo_full)].reset_index(drop=True)
    df_aux_count = (
        df_aux.groupby(["cnes", "profissional_cbo"])
        .size()
        .reset_index(name="quantidade")
    )
    df_pivot = df_aux_count.pivot(
        index="cnes", columns="profissional_cbo", values="quantidade"
    ).fillna(0)

    df_equipes_porcentagem = {
        c: round(len(df_pivot.loc[df_pivot[c] > 0]) / len(df_pivot) * 100, 2)
        for c in df_pivot.columns
    }

    # Geração do pareto! - Refatorar depois!
    labels = list(df_equipes_porcentagem.keys())
    val = list(df_equipes_porcentagem.values())
    total = sum(val)
    acc_val = {labels[i]: round(val[i] / total, 3) for i in range(len(val))}
    dados_pareto_n = dict(
        sorted(df_equipes_porcentagem.items(), key=lambda item: item[1], reverse=True)
    )
    dados_pareto_full = dict(
        sorted(acc_val.items(), key=lambda item: item[1], reverse=True)
    )

    acumulado_freq = np.cumsum(list(dados_pareto_full.values()))
    # Plotando pareto!
    if plota:
        fig, ax1 = plt.subplots()

        # Gráfico de barras
        ax1.bar(
            list(dados_pareto_n.keys()),
            list(dados_pareto_n.values()),
            color="b",
            alpha=0.7,
        )
        ax1.set_xlabel("Categorias")
        ax1.set_ylabel("Frequências")

        # Criando o gráfico da linha acumulada
        ax2 = ax1.twinx()  # Criar um segundo eixo y
        ax2.plot(
            list(dados_pareto_full.keys()),
            acumulado_freq,
            color="r",
            marker="D",
            linestyle="--",
            alpha=0.7,
        )
        ax2.set_ylabel("Percentual Acumulado (%)")

        ax1.tick_params(axis="x", labelrotation=90)
        # Exibindo o gráfico
        plt.title(f"Gráfico de Pareto - Municipio de {municipio}")
        plt.show()

    # indice que representa o valor esperado! - TODO: Tratamento para não quebrar!
    try:
        idx_eqps = next(
            i for i in range(len(acumulado_freq)) if acumulado_freq[i] >= percent
        )
        eqs = list(dados_pareto_n.keys())[: idx_eqps + 1]
    except StopIteration:
        eqs = []

    df_qntd_eq = (
        df_aux.groupby(["cnes", "profissional_cbo"]).agg({"carga_horaria": "sum"})
    ).reset_index()

    df_qntd_eq["qntd_eqs"] = np.ceil(df_qntd_eq.carga_horaria / param_hora)
    return df_qntd_eq, eqs


# %% ########## PRIMÁRIO #############
cidades_iniciais = [
    "IPATINGA",
    "DIVINOPOLIS",
    "CONTAGEM",
    "POCOS DE CALDAS",
    "BELO HORIZONTE",
]

df_eq_prim_aux = pd.DataFrame(
    columns=["cnes", "profissional_cbo", "carga_horaria", "qntd_eqs", "municipio"]
)

for cd in cidades_iniciais:
    df, eqs = retorna_pareto_por_municipio(
        df_eq_primary, cd, percent=0.8, plota=True, param_hora=40, primario=True
    )
    df["municipio"] = cd
    df_eq_prim_aux = pd.concat([df_eq_prim_aux, df])


# %% ########## SECUNDÁRIO #############
cidades_iniciais = [
    "IPATINGA",
    "DIVINOPOLIS",
    "CONTAGEM",
    "POCOS DE CALDAS",
    "BELO HORIZONTE",
]
df_equipes_sec = pd.DataFrame(
    columns=["cnes", "profissional_cbo", "carga_horaria", "qntd_eqs", "municipio"]
)
for cd in cidades_iniciais:
    df, eqs = retorna_pareto_por_municipio(df_eq_sec, cd, percent=0.8, plota=True)
    df["municipio"] = cd
    df_equipes_sec = pd.concat([df_equipes_sec, df])

# %%  ########## TERCIÁRIO #############


cidades_iniciais = [
    "IPATINGA",
    "DIVINOPOLIS",
    "CONTAGEM",
    "POCOS DE CALDAS",
    "BELO HORIZONTE",
]
df_equipes_terc = pd.DataFrame(
    columns=["cnes", "profissional_cbo", "carga_horaria", "qntd_eqs", "municipio"]
)
for cd in cidades_iniciais:
    df, eqs = retorna_pareto_por_municipio(df_eq_ter_aux, cd, percent=0.8, plota=True)
    df["municipio"] = cd
    df_equipes_terc = pd.concat([df_equipes_terc, df])

# %%
df_primary.to_excel("instalacoes_primarias.xlsx")
df_secundary.to_excel("instalacoes_secundarias.xlsx")
df_hospitais_tercearios.to_excel("instalacoes_terciarias.xlsx")

df_eq_prim_aux.to_excel("df_equipes_primario.xlsx")
df_equipes_terc.to_excel("df_equipes_terciario.xlsx")
df_equipes_sec.to_excel("df_equipes_secundario.xlsx")
# %%
df_eq_prim_aux["nivel"] = "primario"
df_equipes_sec["nivel"] = "secundario"
df_equipes_terc["nivel"] = "terciario"

df_end = pd.concat([df_eq_prim_aux, df_equipes_sec, df_equipes_terc])
df_end.to_excel("especialidades_por_nivel_e_municipio.xlsx")
# %%

df_secundary["total"] = (
    df_secundary["MEDICO CARDIOLOGISTA"]
    + df_secundary["MEDICO CLINICO"]
    + df_secundary["MEDICO GINECOLOGISTA E OBSTETRA"]
    + df_secundary["MEDICO ORTOPEDISTA E TRAUMATOLOGISTA"]
    + df_secundary["MEDICO PEDIATRA"]
)

# %%
