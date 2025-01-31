using Pkg
Pkg.add("DataFrames")

using JuMP
using HiGHS
using Plots
using Statistics
using Random
#using StatsKit
using CairoMakie, GeoMakie
using XLSX, DataFrames, CSV
using IterTools
using Distances

Random.seed!(1234)

path_demanda = "dados_cidades_full_MG.xlsx"
path_instalacoes_reais = "dados_instalacoes_saude.csv"
df_demanda = DataFrame(XLSX.readtable(path_demanda, "Sheet1"))
df_instalacoes_reais = DataFrame(CSV.File(path_instalacoes_reais))


municipio = "Divinópolis"
muncipio_MM ="DIVINOPOLIS"
col_demanda = "Total de pessoas"
col_latitude = "Latitude"
col_longitude = "Longitude"
coluna_classificacao_OTM = "classificacao_OTM"
df_inst = df_instalacoes_reais[df_instalacoes_reais.municipio_nome .== muncipio_MM, :]

#Extração dos dados do Dataframe!
df_m = df_demanda[df_demanda.NM_MUN .== municipio, :]
c_demanda = Dict(df_m.CD_SETOR[i] => parse(Int, df_m[!, col_demanda][i]) for i in range(1, length(df_m.CD_SETOR)))
c_coords = Dict(df_m.CD_SETOR[i] => (df_m[!, col_latitude][i], df_m[!, col_longitude][i])  for i in range(1, length(df_m.CD_SETOR)))

#Criação do conjuntos da otimização!
N_qntd_pnts_demanda = length(df_m.CD_SETOR)
S_Demandas = vcat([i for i in values(c_demanda)])
S_Pontos_Demanda = vcat([i for i in range(1, length(df_m.CD_SETOR))])

N_locais_candidatos_full = length(df_m.CD_SETOR)


S_Locais_Candidatos_full = vcat([i for i in range(1, length(df_m.CD_SETOR))])
#S_Locais_Candidatos = vcat(locais_aleatorios)
S_Coordenadas_demandas = vcat([i for i in values(c_coords)])

#Atenção: So funciona nos testes iniciais de todos os pontos de demanda sao locais candidatos!
S_Coordenadas_Candidatos = vcat([i for i in values(c_coords)])

Matriz_Dist = [haversine([c1[1], c1[2]], [c2[1], c2[2]]) for c1 in S_Coordenadas_demandas , c2 in S_Coordenadas_Candidatos]
Dist_Maxima_Demanda_N1 = 20000
custo_abertura = fill(10000000, N_locais_candidatos_full, 1)


#Definição dos locais candidatos!
#nível 1 - UBS
N_locais_candidatos = round(Int, N_qntd_pnts_demanda/20)
locais_aleatorios = unique(rand(1:N_qntd_pnts_demanda, N_locais_candidatos))
S_Locais_Candidatos = S_Locais_Candidatos_full[locais_aleatorios]

#nível 2 - Atenção secundárioa
N_locais_candidatos_n2 = round(Int, N_qntd_pnts_demanda/30)
locais_aleatorios_n2 = unique(rand(1:N_qntd_pnts_demanda, N_locais_candidatos_n2)) #Vou consierar modelo Nested a principio!
S_Locais_Candidatos_n2 = S_Locais_Candidatos_full[locais_aleatorios_n2]

#Nivel 3 - Atenção Terciária
N_locais_candidatos_n3 = min(round(Int, N_qntd_pnts_demanda/100), 3)
locais_aleatorios_n3 = unique(rand(1:N_qntd_pnts_demanda, N_locais_candidatos_n3))
S_Locais_Candidatos_n3 = S_Locais_Candidatos_full[locais_aleatorios_n3]

#tentar dicionario!
dict_teste = Dict(d => [n for n in S_Locais_Candidatos if Matriz_Dist[d,n] <= Dist_Maxima_Demanda_N1] for d in S_Pontos_Demanda)

#Não vou colocar restrição de distância entre primario e secundário!
#matriz_D = Dict((ii,jj) => haversine([c_coords[ii][2], c_coords[ii][1]], [c_coords[jj][2], c_coords[jj][1]]) for ii in S_Setores for jj in S_Setores)

model = JuMP.Model(HiGHS.Optimizer)
set_optimizer_attribute(model, "time_limit", 1500.0)
set_optimizer_attribute(model, "primal_feasibility_tolerance", 1e-6)
set_optimizer_attribute(model, "mip_rel_gap", 0.1) 

#Pensar em como criar essa variável como matriz!
var_fluxo_n1 = @variable(model, atr_[d in S_Pontos_Demanda, k in dict_teste[d]], Bin)
abertura_n1 = @variable(model, abr_[S_Locais_Candidatos], Bin)


var_fluxo_n1_n2 = @variable(model, atr_N2_[S_Locais_Candidatos, S_Locais_Candidatos_n2] >= 0)
abertura_n2 = @variable(model, abr_N2_[S_Locais_Candidatos_n2], Bin)


var_fluxo_n2_n3 = @variable(model, atr_N3_[S_Locais_Candidatos_n2, S_Locais_Candidatos_n3] >= 0)
abertura_n3 = @variable(model, abr_N3_[S_Locais_Candidatos_n3], Bin)

#Função objetivo!
#Custos Aberturas!
@expression(model, custo_abertura_instalacao_n1, sum(abr_[s] * custo_abertura[s] for s in S_Locais_Candidatos) )
@expression(model, custo_abertura_instalacao_n2, sum(abr_N2_[s] * custo_abertura[s] for s in S_Locais_Candidatos_n2) )
@expression(model, custo_abertura_instalacao_n3, sum(abr_N3_[s] * custo_abertura[s] * 100 for s in S_Locais_Candidatos_n3))
@expression(model, custo_aberturas, custo_abertura_instalacao_n1 + custo_abertura_instalacao_n2 + custo_abertura_instalacao_n3)

#Custos Sociais!
@expression(model, custo_social_n1, sum(atr_[i,j] * Matriz_Dist[i,j] for i in S_Pontos_Demanda for j in dict_teste[i]))
@expression(model, custo_social_n2, sum(atr_N2_[i,j] * Matriz_Dist[i,j] for i in  S_Locais_Candidatos, j in S_Locais_Candidatos_n2))
@expression(model, custo_social_n3, sum(atr_N3_[i,j] * Matriz_Dist[i,j] for i in S_Locais_Candidatos_n2, j in S_Locais_Candidatos_n3))
@expression(model, custo_social, custo_social_n1 + custo_social_n2 + custo_social_n3)

@objective(model, Min, custo_social + custo_aberturas)


#Restrições:
#Conservação de FLuxos
@constraint(model, demandan1[d in S_Pontos_Demanda], sum(atr_[d, :]) == 1)
@constraint(model, fluxodemandaN1_N2[s in S_Locais_Candidatos], sum(atr_[d,s] * S_Demandas[d] for d in S_Pontos_Demanda if s in dict_teste[d]) * 0.4 == 
                                                                sum(atr_N2_[s, n2] for n2 in S_Locais_Candidatos_n2)) #preciso saber todos os pontos que podem ser atendidos pelo local S!

@constraint(model, fluxodemandaN2_N3[n2 in S_Locais_Candidatos_n2], sum(atr_N2_[n1,n2] for n1 in S_Locais_Candidatos) == 0.3 * sum(atr_N3_[n2, n3] for n3 in S_Locais_Candidatos_n3))

#Abertura pontos!
@constraint(model, abertura[s in S_Locais_Candidatos], sum(atr_[d,s] * S_Demandas[d] for d in S_Pontos_Demanda if s in dict_teste[d]) <= abr_[s] * 10000)
@constraint(model, aberturaN2[n2 in S_Locais_Candidatos_n2], sum(atr_N2_[s, n2] for s in S_Locais_Candidatos) <= abr_N2_[n2] * 120000)
@constraint(model, aberturaN3[n3 in S_Locais_Candidatos_n3], sum(atr_N3_[n2, n3] for n2 in S_Locais_Candidatos_n2) <= abr_N3_[n3] * 800000)

optimize!(model)

obj = objective_value(model)


#Pós-Otimização:
#Bases abertas
bases_abertura = [(v, value(v)) for v in abertura_n1 if value(v) > 0]
atr_demanda_n1 = [v for v in var_fluxo_n1 if value(v) > 0]


#Abertura n2!
bases_abertura_n2 = [(v, value(v)) for v in abertura_n2 if value(v) > 0]
atr_demanda_n1_n2 = [(v, value(v)) for v in var_fluxo_n1_n2 if value(v) > 0]


#Abertura n3!
bases_abertura_n3 = [(v, value(v)) for v in abertura_n3 if value(v) > 0]
atr_demanda_n2_n3 = [(v, value(v)) for v in var_fluxo_n2_n3 if value(v) > 0]