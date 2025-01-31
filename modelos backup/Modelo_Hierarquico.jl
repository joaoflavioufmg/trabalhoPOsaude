using Pkg
#Pkg.add("DataFrames")

using DataFrames
using JuMP
using HiGHS
using Plots
using Statistics
using Random
using StatsKit
using CairoMakie, GeoMakie


#Dados input
qntd_pontos_demanda = 10
qntd_atencao_lvl_1 = 5
qntd_atencao_lvl_2 = 3

n_PCF_level_1 = 4
n_PCF_level_2 = 2

distancia_demanda_pcf_1_aux = [
    [35, 44, 98, 87, 61],
    [70, 91, 84, 77, 95],
    [86, 89, 30, 63, 91],
    [57, 98, 90, 95, 85],
    [79, 99, 45, 41, 99],
    [62, 68, 79, 42, 70],
    [61, 69, 79, 52, 77],
    [84, 89, 50, 57, 42],
    [74, 40, 49, 91, 41],
    [59, 37, 39, 50, 64]
]

distancia_pcf_1_pdf_2_aux = [
    [43, 38, 82],
    [54, 71, 59],
    [100, 78, 68],
    [59, 96, 58],
    [38, 66, 50]
]

demanda_origem_aux = [53,47,42,49,46,35,50,47,52,36]
capacidade_lvl_1_aux = [148,132,163,140,158]
capacidade_lvl_2_aux = [257,244,253]

pacientes_encaminhados_aux = [1, 0.7, 0.8, 0.8, 0.5]


#Criação dos conjuntos
s_ponto_demanda = [i for i in range(1, qntd_pontos_demanda)]
s_lvl_1 = [i for i in range(1, qntd_atencao_lvl_1)]
s_lvl_2 = [i for i in range(1, qntd_atencao_lvl_2)]

distancia_demanda_lvl_1 = Dict((i,j) => distancia_demanda_pcf_1_aux[i][j] for i in s_ponto_demanda for j in s_lvl_1)
distancia_lvl_1_lvl_2 = Dict((i,j) => distancia_pcf_1_pdf_2_aux[i][j] for i in s_lvl_1 for j in s_lvl_2)
demanda = Dict(i => demanda_origem_aux[i] for i in s_ponto_demanda)
capacidade_lvl_1 = Dict(i => capacidade_lvl_1_aux[i] for i in s_lvl_1)
capacidade_lvl_2 = Dict(i => capacidade_lvl_2_aux[i] for i in s_lvl_2)
pacientes_encaminhados = Dict(i => pacientes_encaminhados_aux[i] for i in s_lvl_1)

#Criação do Modelo
model = JuMP.Model(HiGHS.Optimizer)

#Criacao das Variaveis

#Abertura nivel 1
abertura_lvl_1 = @variable(model, abr_lvl_1[i ∈ s_lvl_1], Bin)

#Abertura nivel 2
abertura_lvl_2 = @variable(model, abr_lvl_2[i ∈ s_lvl_2], Bin)

#Fluxo da quantidade pacientes da demanda para nível 1
pacientes_demanda_lvl_1 = @variable(model, fluxo_demanda_lvl_1[i ∈ s_ponto_demanda, j ∈ s_lvl_1] >= 0)

#Fluxo da quantidade de pacientes lvl 1 - lvl 2
pacientes_lvl_1_lvl_2 = @variable(model, fluxo_lvl_1_lvl_2[i ∈ s_lvl_1, j ∈ s_lvl_2] >= 0)

#Função objetivo - usando expression
#Distancia da demanda até lvl 1
@expression(model, distancia_demanda_lvl_1_obj, sum(fluxo_demanda_lvl_1[i,j] * distancia_demanda_lvl_1[i,j] for i in s_ponto_demanda for j in s_lvl_1))

#Distancia do lvl 1 até lvl 2
@expression(model, distancia_lvl_1_lvl_2_obj, sum(fluxo_lvl_1_lvl_2[i,j] * distancia_lvl_1_lvl_2[i,j] for i in s_lvl_1 for j in s_lvl_2))

#objetivo
@objective(model, Min, distancia_demanda_lvl_1_obj + distancia_lvl_1_lvl_2_obj)


#Restrições!!
#Toda a demanda precisa ser atendida nos pontos lvl 1
@constraint(model, [i ∈ s_ponto_demanda], sum(fluxo_demanda_lvl_1[i, j] for j in s_lvl_1) == demanda[i])

#Toda a demanda que sai do lvl 1 precisa ser atendida no lvl 2
@constraint(model, [k ∈ s_lvl_1], sum(fluxo_lvl_1_lvl_2[k, j] for j in s_lvl_2) == pacientes_encaminhados[k] * sum(fluxo_demanda_lvl_1[i,k] for i in s_ponto_demanda))

#Restricao de Capacidade do lvl 1. Preciso multiplicar pela abertura para ativar o fluxo naquela unidade?
@constraint(model, [k ∈ s_lvl_1], sum(fluxo_demanda_lvl_1[i,k] for i in s_ponto_demanda) <= capacidade_lvl_1[k] * abr_lvl_1[k])

#Restrição de capacidade do lvl 2
@constraint(model, [j ∈ s_lvl_2], sum(fluxo_lvl_1_lvl_2[k,j] for k in s_lvl_1) <= capacidade_lvl_2[j] * abr_lvl_2[j])

#Garantia da quantidade de aberturas lvl 1
@constraint(model, sum(abr_lvl_1[k] for k in s_lvl_1) == n_PCF_level_1)

#Garantia da quantidade de aberturas lvl 2
@constraint(model, sum(abr_lvl_2[j] for j in s_lvl_2) == n_PCF_level_2)


optimize!(model)

#funcao_objetivo 
obj = objective_value(model)

#lvl 1 abertos
resultado_abertura_lvl_1 = [p for p in abertura_lvl_1 if value(p) > 0]
resultado_abertura_lvl_2 = [p for p in abertura_lvl_2 if value(p) > 0]

#fluxo lvl 1
resultado_fluxo_demanda_lvl_1 = [(p, value(p)) for p in pacientes_demanda_lvl_1 if value(p) > 0]
resultado_fluxo_lvl1_lvl2 = [(p, value(p)) for p in pacientes_lvl_1_lvl_2 if value(p) > 0]


