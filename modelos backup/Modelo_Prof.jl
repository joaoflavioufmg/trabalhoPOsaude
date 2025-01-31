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


n_demanda = 15
n_niveis = 3
n_tipos_paciente = 1

n_eq_n1 = 4
n_eq_n2 = 5
n_eq_n3 = 5

n_existe_n1 = 6
n_existe_n2 = 4
n_existe_n3 = 3

n_candidatos_n1 = 10
n_candidatos_n2 = 8
n_candidatos_n3 = 6

S_demanda = vcat([i for i in range(1,n_demanda )])
S_niveis = vcat([i for i in range(1,n_niveis )])
S_pacientes = vcat([i for i in range(1,n_tipos_paciente )])

S_eq_n1 = vcat([i for i in range(1,n_eq_n1 )])
S_eq_n2 = vcat([i for i in range(1,n_eq_n2 )])
S_eq_n3 = vcat([i for i in range(1,n_eq_n3 )])

S_locais_existentes_n1 = vcat([i for i in range(1,n_existe_n1 )])
S_locais_existentes_n2 = vcat([i for i in range(1,n_existe_n2 )])
S_locais_existentes_n3 = vcat([i for i in range(1,n_existe_n3 )])

S_locais_candidatos_n1 = vcat([i for i in range(n_existe_n1 + 1, n_candidatos_n1 )])
S_locais_candidatos_n2 = vcat([i for i in range(n_existe_n2 +1 , n_candidatos_n2 )])
S_locais_candidatos_n3 = vcat([i for i in range(n_existe_n3 +1 , n_candidatos_n3 )])


S_n1 = vcat(S_locais_existentes_n1, S_locais_candidatos_n1)
S_n2 = vcat(S_locais_existentes_n2, S_locais_candidatos_n2)
S_n3 = vcat(S_locais_existentes_n3, S_locais_candidatos_n3)

n_locais_n1 = 10
n_locais_n2 = 8
n_locais_n3 = 6

S_custo_equipe_n1 = fill(10, n_eq_n1)
S_custo_equipe_n2 = fill(20, n_eq_n2)
S_custo_equipe_n3 = fill(30, n_eq_n3)

S_dist_n1 = fill(1, n_demanda, n_locais_n1 )
S_dist_n2 = fill(1, n_locais_n1, n_locais_n2 )
S_dist_n3 = fill(1, n_locais_n2, n_locais_n3 )

S_custo_desloc_n1 = fill(1, n_demanda, n_locais_n1 )
S_custo_desloc_n2 = fill(1, n_locais_n1, n_locais_n2 )
S_custo_desloc_n3 = fill(1, n_locais_n2, n_locais_n3 )

S_custo_variavel_n1 = fill(5, n_tipos_paciente, n_locais_n1 )
S_custo_variavel_n2 = fill(10, n_tipos_paciente, n_locais_n2 )
S_custo_variavel_n3 = fill(20, n_tipos_paciente, n_locais_n3 )

S_custo_fixo_n1 = fill(1000, n_locais_n1)
S_custo_fixo_n2 = fill(200, n_locais_n2)
S_custo_fixo_n3 = fill(300, n_locais_n3)

#S_pop_n1 = hcat(fill(100, n_demanda), fill(200, n_demanda))
S_pop_n1 = fill(300, n_demanda)

S_Nec_eq_n1 = vcat([2*10^-2, 2*10^-3, 2*10^-3, 2*10^-3])
S_Nec_eq_n2 = vcat([1*10^-2, 1*10^-2, 1*10^-2, 1*10^-2, 1*10^-2])
S_Nec_eq_n3 = vcat([1*10^-2, 2*10^-2, 1*10^-2, 2*10^-2, 1*10^-2])

S_CNES_n1 = fill(5, n_eq_n1, n_existe_n1 )
S_CNES_n2 = fill(3, n_eq_n2, n_existe_n2 )
S_CNES_n3 = fill(2, n_eq_n3, n_existe_n3 )

S_cap_por_nivel_n1 = transpose(hcat(vcat([1000, 1000,1000,1000,1000,1000,1000, 500, 500, 500  ]), 
                            vcat([1000, 1000,1000,1000,1000,1000,1000, 500, 500, 500  ])))

S_cap_n2 = vcat([1000, 100, 100, 200, 200, 200, 200, 200])
S_cap_n3 = vcat([300, 300, 300, 300, 300, 300])

max_abr_n1 = 4
max_abr_n2 = 3
max_abr_n3 = 2

P_n1_n2 = 0.4
P_n2_n3 = 0.7


model = JuMP.Model(HiGHS.Optimizer)

#Variaveis de fluxo
fluxo_n1 = @variable(model, X_n1[d in S_demanda, n1 in S_n1, p in S_pacientes] >= 0) #Usei o indice P aqui para calcular fluxo!
fluxo_n2 = @variable(model, X_n2[n1 in S_n1, n2 in S_n2, p in S_pacientes] >= 0)
fluxo_n3 = @variable(model, X_n3[n1 in S_n2, n2 in S_n3, p in S_pacientes] >= 0)

#Abertura unidades
abr_candidatos_n1 = @variable(model, Abr_n1[n1 in S_locais_candidatos_n1], Bin)
abr_candidatos_n2 = @variable(model, Abr_n2[n2 in S_locais_candidatos_n2], Bin)
abr_candidatos_n3 = @variable(model, Abr_n3[n3 in S_locais_candidatos_n3], Bin)

#Fluxo equipes
fluxo_eq_n1 = @variable(model, eq_n1[eq in S_eq_n1, n1 in S_n1])
fluxo_eq_n2 = @variable(model, eq_n2[eq in S_eq_n2, n1 in S_n2])
fluxo_eq_n3 = @variable(model, eq_n3[eq in S_eq_n3, n1 in S_n3])

#Restrições fluxo
@constraint(model, [d in S_demanda, p in S_pacientes], S_pop_n1[d,p] == sum(X_n1[d, n1, p] for n1 in S_n1))
@constraint(model, [n1 in S_n1, p in S_pacientes], sum(X_n2[n1, n2, p] for n2 in S_n2) == sum(X_n1[d, n1, p] for d in S_demanda) * P_n1_n2)
@constraint(model, [n2 in S_n2, p in S_pacientes], sum(X_n3[n2, n3, p] for n3 in S_n3) == sum(X_n2[n1, n2, p] for n1 in S_n1) * P_n2_n3)


#Restricoes abertura de novas unidades
@constraint(model, [un in S_locais_candidatos_n1], sum(X_n1[d, un, p] for d in S_demanda, p in S_pacientes) <= sum(S_pop_n1[:]) * Abr_n1[un])
@constraint(model, [un in S_locais_candidatos_n2], sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes) <= sum(S_pop_n1[:]) * Abr_n2[un])
@constraint(model, [un in S_locais_candidatos_n3], sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes) <= sum(S_pop_n1[:]) * Abr_n3[un])

#Abertura Máxima de novas unidades
@constraint(model, sum(Abr_n1[un] for un in S_locais_candidatos_n1) <= max_abr_n1)
@constraint(model, sum(Abr_n2[un] for un in S_locais_candidatos_n2) <= max_abr_n2)
@constraint(model, sum(Abr_n3[un] for un in S_locais_candidatos_n3) <= max_abr_n3)

#Capacidade das Unidades!

@constraint(model, [n1 in S_n1, p in S_pacientes], sum(X_n1[d, n1, p] for d in S_demanda) <= S_cap_por_nivel_n1[p, n1])
@constraint(model, [n2 in S_n2], sum(X_n2[n1,n2, p] for n1 in S_n1, p in S_pacientes) <= S_cap_n2[n2])
@constraint(model, [n3 in S_n3], sum(X_n3[n2, n3, p] for n2 in S_n2, p in S_pacientes) <= S_cap_n3[n3])

#Capacidade das equipes
 #Bases que não existem tem profissionais???
@constraint(model, [eq in S_eq_n1, un in S_locais_existentes_n1], 
                  S_CNES_n1[eq, un] + fluxo_eq_n1[eq,un] == sum(X_n1[d, un, p] for d in S_demanda, p in S_pacientes) * S_Nec_eq_n1[eq])


@constraint(model, [eq in S_eq_n1, un in S_locais_candidatos_n1], 
                    fluxo_eq_n1[eq,un] == sum(X_n1[d, un, p] for d in S_demanda, p in S_pacientes) * S_Nec_eq_n1[eq])



@constraint(model, [eq in S_eq_n2, un in S_locais_existentes_n2],
                    S_CNES_n2[eq, un] + fluxo_eq_n2[eq,un] == sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes) * S_Nec_eq_n2[eq])


@constraint(model, [eq in S_eq_n2, un in S_locais_candidatos_n2],
                     fluxo_eq_n2[eq,un] == sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes) * S_Nec_eq_n2[eq])
    

@constraint(model, [eq in S_eq_n3, un in S_locais_existentes_n3],
                     S_CNES_n3[eq, un] + fluxo_eq_n3[eq,un] == sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes) * S_Nec_eq_n3[eq])
                     

@constraint(model, [eq in S_eq_n3, un in S_locais_candidatos_n3],
                    fluxo_eq_n3[eq,un] == sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes) * S_Nec_eq_n3[eq])
                    
                    

#Funcoes Objetivo!
@expression(model, custo_logistico_n1,  sum(X_n1[d, un, p] * S_dist_n1[d, un] * S_custo_desloc_n1[d,un] for d in S_demanda, un in S_n1, p in S_pacientes))
@expression(model, custo_fixo_novos_n1, sum(Abr_n1[un] * S_custo_fixo_n1[un] for un in S_locais_candidatos_n1))
@expression(model, custo_fixo_existente_n1, sum(S_custo_fixo_n1[un1] for un1 in S_locais_existentes_n1))
@expression(model, custo_times_novos_n1, sum(fluxo_eq_n1[eq, un] * S_custo_equipe_n1[eq] for eq in S_eq_n1, un in S_n1))
@expression(model, custo_variavel_n1, sum(X_n1[d, un, p] * S_custo_variavel_n1[p,un] for d in S_demanda, un in S_n1, p in S_pacientes))

@expression(model, custo_logistico_n2,  sum(X_n2[un, un2, p] * S_dist_n2[un, un2] * S_custo_desloc_n2[un, un2] for un2 in S_n2, un in S_n1, p in S_pacientes))
@expression(model, custo_fixo_novos_n2, sum(Abr_n2[un] * S_custo_fixo_n2[un] for un in S_locais_candidatos_n2))
@expression(model, custo_fixo_existente_n2, sum(S_custo_fixo_n2[un2] for un2 in S_locais_existentes_n2))
@expression(model, custo_times_novos_n2, sum(fluxo_eq_n2[eq, un] * S_custo_equipe_n2[eq] for eq in S_eq_n2, un in S_n2))
@expression(model, custo_variavel_n2, sum(X_n2[un,un2, p] * S_custo_variavel_n2[p,un2] for un2 in S_n2, un in S_n1, p in S_pacientes))


@expression(model, custo_logistico_n3,  sum(X_n3[un2, un3, p] * S_dist_n3[un2, un3] * S_custo_desloc_n3[un2, un3] for un2 in S_n2, un3 in S_n3, p in S_pacientes))
@expression(model, custo_fixo_novos_n3, sum(Abr_n3[un] * S_custo_fixo_n3[un] for un in S_locais_candidatos_n3))
@expression(model, custo_fixo_existente_n3, sum(S_custo_fixo_n3[un3] for un3 in S_locais_existentes_n3))
@expression(model, custo_times_novos_n3, sum(fluxo_eq_n3[eq, un] * S_custo_equipe_n3[eq] for eq in S_eq_n3, un in S_n3))
@expression(model, custo_variavel_n3, sum(X_n3[un2,un3, p] * S_custo_variavel_n3[p,un3] for un2 in S_n2, un3 in S_n3, p in S_pacientes))


@expression(model, custo_logistico, custo_logistico_n1 + custo_logistico_n2 + custo_logistico_n3)
@expression(model, custo_fixo_novo, custo_fixo_novos_n1 + custo_fixo_novos_n2 + custo_fixo_novos_n3 )
@expression(model, custo_fixo_existente, custo_fixo_existente_n1 + custo_fixo_existente_n2 + custo_fixo_existente_n3)
@expression(model, custo_times_novos, custo_times_novos_n1 + custo_times_novos_n2 + custo_times_novos_n3)
@expression(model, custo_variavel, custo_variavel_n1 + custo_variavel_n2 + custo_variavel_n3)

@objective(model, Min, custo_logistico + custo_fixo_novo + custo_fixo_existente + custo_times_novos +  custo_variavel)

optimize!(model)
obj = objective_value(model)

println("RELATIORIO DE CUSTOS")
println(string("Custo Logistico: ", value(custo_logistico)))
println(string("Custo Fixo Novas Instalacoes: ", value(custo_fixo_novo)))
println(string("Custo Fixo Instalacoes Existentes: ", value(custo_fixo_existente)))
println(string("Custo Times Novos: ", value(custo_times_novos)))
println(string("Custo Variável: ", value(custo_variavel)))
println(string("Custo Total: ", value(objective_value(model))))


println("=========================================================")
println("Abertura de unidades N1")
for i in S_locais_candidatos_n1
    if value(Abr_n1[i]) == 0
        continue
    end
    println(string("Local: ", i , "Aberto"))
end

println("=========================================================")
println("Abertura de unidades N2")
for i in S_locais_candidatos_n2
    if value(Abr_n2[i]) == 0
        continue
    end
    println(string("Local: ", i , " Aberto"))
end


println("=========================================================")
println("Abertura de unidades N3")
for i in S_locais_candidatos_n3
    if value(Abr_n3[i]) <= 0.1
        continue
    end
    println(string("Local: ", i , " Aberto",  value(Abr_n3[i])))
end

println("=========================================================")
println("Atendimento Demanda n1")
for d in S_demanda
    v = sum(value(X_n1[d,n,p]) for n in S_n1, p in S_pacientes)
    println(string("Demanda ", d, " Valor ", v))
end



println("=========================================================")
println("Fluxo Nível primário")

for d in S_demanda, un in S_n1, p in S_pacientes
    if value(fluxo_n1[d,un,p]) == 0
        continue
    end
    println(string("Origem: ", d, ", Destino: ", un ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n1[d,un,p]) ))
end

println("=========================================================")
println("Fluxo Nível Secundário")

for un in S_n1, un2 in S_n2, p in S_pacientes
    if value(fluxo_n2[un,un2,p]) <= 0.1
        continue
    end
    println(string("Origem: ", un, ", Destino: ", un2 ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n2[un,un2,p]) ))
end

println("=========================================================")
println("Fluxo Nível Terciario")
for un2 in S_n2, un3 in S_n3,p in S_pacientes
    if value(fluxo_n3[un2,un3, p]) == 0
        continue
    end
    println(string("Origem: ", un2, ", Destino: ", un3 ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n3[un2,un3, p]) ))
end


print("=========================================================")
println("Fluxo Equipes Primário")

for n in S_n1, eq in S_eq_n1
    if value(fluxo_eq_n1[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n1[eq, n]) ))
end


println("=========================================================")
println("Fluxo Equipes Secundário")

for n in S_n2, eq in S_eq_n2
    if value(fluxo_eq_n2[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n2[eq, n]) ))
end


println("=========================================================")
println("Fluxo Equipes Terciário")

for n in S_n3, eq in S_eq_n3
    if value(fluxo_eq_n3[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n3[eq, n]) ))
end



println("=========================================================")
println("Capacidades usadas N1")

for n in S_n1
    v = sum(value(X_n1[d,n,p]) for d in S_demanda, p in S_pacientes)
    println(string("Facility ", n, " Valor ", v))
end


println("=========================================================")
println("Capacidades usadas N2")

for n in S_n2
    v = sum(value(X_n2[n1,n,p]) for n1 in S_n1, p in S_pacientes)
    println(string("Facility ", n, " Valor ", v))
end


println("=========================================================")
println("Capacidades usadas N3")

for n in S_n3
    v = sum(value(X_n3[n2,n,p]) for n2 in S_n2, p in S_pacientes)
    println(string("Facility ", n, " Valor ", v))
end


