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


h = 2
qntd_n1 = 10
qntd_candidate_n2 = 15
qntd_n3 = 3

S_tipos = [i for i in range(1, h)]
S_n1 = [i for i in range(1, qntd_n1)]
S_n2 = [i for i in range(1, qntd_candidate_n2)]
S_n3 =  [i for i in range(1, qntd_n3)]
custo_n1_n2 = 1
custo_n2_n3 = 2
custo_variavel_paciente_n2 = 10
custo_fixo_n2 = 500
cap_n2 = 50
cap_n1 = 50

#Matrizes tem estrutura da linha como origem e coluna como destino!
custo_dist_n1_n2 = fill(custo_n1_n2, h, qntd_n1, qntd_candidate_n2)
custo_dist_n2_n3 = fill(custo_n2_n3, h, qntd_candidate_n2, qntd_n3)

custo_variavel_paciente_n2 = fill(custo_variavel_paciente_n2, h, qntd_candidate_n2)

#custo_fixo_n2 = [custo_fixo_n2 for i in S_n2]
mat_custo_fixo_n2 = fill(custo_fixo_n2, qntd_candidate_n2, 1)
capacidade_n2 = [cap_n2 for i in S_n2]


lista_demanda_hospital =[[50,100,150]
                        [100,150,200]]

#linha - tipo paciente, colunas - hospitais
demanda_hospital = reshape(reduce(vcat, lista_demanda_hospital), (2, 3))
capacidade_paciente_n1 = fill(cap_n1, h, qntd_n1)


model = JuMP.Model(HiGHS.Optimizer)

var_fluxo_n1_n2_n3 = @variable(model, x[h ∈ S_tipos, i ∈ S_n1, j ∈ S_n2, k ∈ S_n3] >= 0)
abertura_n2 = @variable(model, z[j ∈ S_n2], Bin)

#custo de viajem dos pacientes!

@expression(model, custo_transporte, sum((custo_dist_n1_n2[h, i, j] + custo_dist_n2_n3[h,j,k]) * x[h,i,j,k] 
                                    for h in S_tipos, i in S_n1, j in S_n2, k in S_n3))
@expression(model, custo_abertura, sum(z[j] * mat_custo_fixo_n2[j,1] for j in S_n2))
@expression(model, custo_variavel_atendimento, sum(custo_variavel_paciente_n2[h,j] * x[h,i,j,k] for h in S_tipos, i in S_n1, j in S_n2, k in S_n3))
@objective(model, Min, custo_transporte + custo_variavel_atendimento + custo_abertura)


#RESTRIÇÕES

@constraint(model, [h ∈ S_tipos, k ∈ S_n3], sum(x[h,i,j,k] for i in S_n1, j in S_n2) == demanda_hospital[h,k])

@constraint(model, [h ∈ S_tipos, i ∈ S_n1], sum(x[h,i,j,k] for j in S_n2, k in S_n3) <= capacidade_paciente_n1[h,i])

@constraint(model, [j ∈ S_n2], sum(x[h,i,j,k] for h ∈ S_tipos, i ∈ S_n1, k ∈ S_n3) <=  capacidade_n2[j] * z[j])

optimize!(model)

#funcao_objetivo
#Questão 1: 
obj = objective_value(model)

#Questão 2: porcentagem do uso do n1 = quantidade de pacientes / Capacidade total 
utl_por_n1 = Dict(i => sum(value(v) for v in var_fluxo_n1_n2_n3[:, i, :, :]) for i in S_n1)
total_utl = sum(utl_por_n1[i] for i in S_n1)
cap_total_n1 = sum(capacidade_paciente_n1)
utilizacao_global = total_utl/cap_total_n1



#Questão 3 custo de transporte:
custo_transporte = sum((custo_dist_n1_n2[h, i, j] + custo_dist_n2_n3[h,j,k]) * value(x[h,i,j,k]) 
                                    for h in S_tipos, i in S_n1, j in S_n2, k in S_n3)


#Questão 4: Utilizacao Nivel 2
utl_por_n2 = Dict(i => sum(value(v) for v in var_fluxo_n1_n2_n3[:, :, i, :]) for i in S_n2)
total_ut2 = sum(utl_por_n1[i] for i in S_n2)
cap_total_n2 = sum(capacidade_n2)
utl_n2 = total_ut2 / cap_total_n2
println(utl_por_n2)


#Questão 6:
utl_por_n3 = Dict(i => sum(value(v) for v in var_fluxo_n1_n2_n3[:, :, :, i]) for i in S_n3)