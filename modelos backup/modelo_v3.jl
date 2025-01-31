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

############################# LEITURA DOS DADOS #############################
path_demanda = "dados_PRONTOS_para_modelo_OTM//dados_cidades_full_MG.xlsx"
path_instalacoes_reais = "dados_PRONTOS_para_modelo_OTM//dados_instalacoes_saude.csv"
df_demanda = DataFrame(XLSX.readtable(path_demanda, "Sheet1"))
df_ins_prim = DataFrame(XLSX.readtable("dados_PRONTOS_para_modelo_OTM//instalacoes_primarias.xlsx", "Sheet1"))
df_ins_sec = DataFrame(XLSX.readtable("dados_PRONTOS_para_modelo_OTM//instalacoes_secundarias.xlsx", "Sheet1"))
df_ins_ter = DataFrame(XLSX.readtable("dados_PRONTOS_para_modelo_OTM//instalacoes_terciarias.xlsx", "Sheet1"))
df_equipes_primario = DataFrame((XLSX.readtable("dados_PRONTOS_para_modelo_OTM//equipes_Primario_FIM _COMPLETO.xlsb.xlsx", "dados_modelo")))
df_equipes = select(df_equipes_primario, [:cnes, :ESF, :ESB, :EACS, :EAP]) #filtrando dados para facilitar o merge!
df_necessidades_primario = DataFrame((XLSX.readtable("dados_PRONTOS_para_modelo_OTM//equipes_Primario_FIM _COMPLETO.xlsb.xlsx", "necessidades_pop")))


############################# Set dos Municipios #############################
municipio = "Ipatinga"
muncipio_MM = uppercase(municipio) #colocar função semelhante ao .upper do python
col_demanda = "Total de pessoas"
col_latitude = "Latitude"
col_longitude = "Longitude"


############################# Filtro dos dados do municipio #############################
#Extração dos dados do Dataframe!
df_m = df_demanda[df_demanda.NM_MUN .== municipio, :]
#c_demanda = Dict(df_m.CD_SETOR[i] => parse(Int, df_m[!, col_demanda][i]) for i in range(1, length(df_m.CD_SETOR)))
c_demanda = Dict(df_m.CD_SETOR[i] => df_m[!, col_demanda][i] for i in range(1, length(df_m.CD_SETOR)))
c_coords = Dict(df_m.CD_SETOR[i] => (df_m[!, col_latitude][i], df_m[!, col_longitude][i])  for i in range(1, length(df_m.CD_SETOR)))

df_n1 = df_ins_prim[df_ins_prim.municipio_nome .== muncipio_MM, :]
df_n1 = leftjoin(df_n1, df_equipes, on = :cnes)
dropmissing!(df_n1)
df_n2 = df_ins_sec[df_ins_sec.municipio_nome .== muncipio_MM, :]
df_n3 = df_ins_ter[df_ins_ter.municipio_nome .== muncipio_MM, :]




############################# Definição dos Conjuntos #############################

qntd_n1_real = length(df_n1.nome_fantasia)
qntd_n1_candidato = length(df_m.CD_SETOR)
qntd_n2_real = length(df_n2.nome_fantasia)
qntd_n2_candidato = length(df_m.CD_SETOR)
qntd_n3_real = length(df_n3.nome_fantasia)
qntd_n3_candidato = length(df_m.CD_SETOR)

############################# Definição das Equipes #############################

############### NÍVEL PRIMÁRIO ###############

lista_equipes_n1 = df_necessidades_primario[!, "Equipe"]
qntd_equipes_n1 = length(lista_equipes_n1)
S_equipes = vcat([i for i in range(1, qntd_equipes_n1)])
pop_maxima_por_equipe_n1 = df_necessidades_primario[!, "Necessidade"]
capacidade_maxima_por_equipe_n1 = vcat([1/v for v in pop_maxima_por_equipe_n1]) #Quantidade máxima que cada equipe pode atender!

qntd_equipes_por_n1 = Matrix(select(df_n1, [:ESF, :ESB, :EACS, :EAP]))



############### NÍVEL Secundário ###############
#TODO: Para o nível secundário, vou tratar a análise de acordo com os níveis das instalações!
#TODO: Novamente, posso só atribuir e no pós-OTM definir a classificação da unidade de saúde, mas na v0 vou tentar usar as classificações e fazer rodada fixando essas capacidades para ver se o modelo readequa e entrega resultado!

lista_equipes_n2 = ["MEDICO CARDIOLOGISTA",	"MEDICO CLINICO", "MEDICO GINECOLOGISTA E OBSTETRA","MEDICO ORTOPEDISTA E TRAUMATOLOGISTA", "MEDICO PEDIATRA"]

qntd_equipes_n2 = length(lista_equipes_n2)
S_equipes_n2 = vcat([i for i in range(1, qntd_equipes_n2)])
#Dados aqui vão ser de capacidade!
S_capacidade_CNES_n2 = Matrix(select(df_n2, [:"MEDICO CARDIOLOGISTA", :"MEDICO CLINICO", :"MEDICO GINECOLOGISTA E OBSTETRA", :"MEDICO ORTOPEDISTA E TRAUMATOLOGISTA", :"MEDICO PEDIATRA"]))
 #Equipe, instalação
#S_porte_instalacao_real_n2 = vcat([capacidade_maxima_por_equipe_n2[i] for i in df_n2[!,"classificacao_Sec"]])
S_eq_por_paciente_n2 = vcat([1*10^-2 for _ in lista_equipes_n2])


############### NÍVEL Terciário ###############
lista_equipes_n3 = ["MEDICO ANESTESIOLOGISTA", "MEDICO CIRURGIAO GERAL", "MEDICO EM CIRURGIA VASCULAR", "MEDICO NEUROLOGISTA", 	"MEDICO OFTALMOLOGISTA", "MEDICO OTORRINOLARINGOLOGISTA",  "MEDICO UROLOGISTA"]

qntd_equipes_n3 = length(lista_equipes_n3)
S_equipes_n3 = vcat([i for i in range(1, qntd_equipes_n3)])
S_capacidade_CNES_n3 = Matrix(select(df_n3, [:"MEDICO ANESTESIOLOGISTA", :"MEDICO CIRURGIAO GERAL", :"MEDICO EM CIRURGIA VASCULAR", :"MEDICO NEUROLOGISTA", :"MEDICO OFTALMOLOGISTA", :"MEDICO OTORRINOLARINGOLOGISTA", :"MEDICO UROLOGISTA"]))
S_eq_por_paciente_n3 = vcat([2*10^-2 for _ in lista_equipes_n3])


lista_doencas = ["Crônico", "Agudo"]
porcentagem_populacao = [0.54, 0.46]


S_instalacoes_reais_n1 = vcat([i for i in range(1, qntd_n1_real)])
S_relacao_UBS_SC = vcat([findfirst(x -> x == i, df_n1.cnes) for i in df_m.UBS_ref]) #Montar tratamentos no python depois para isso
S_instalacoes_reais_n2 = vcat([i for i in range(1, qntd_n2_real)])
S_instalacoes_reais_n3 = vcat([i for i in range(1, qntd_n3_real)])

S_locais_candidatos_n1 = vcat([i for i in range(qntd_n1_real + 1, qntd_n1_candidato + qntd_n1_real)])
S_locais_candidatos_n2 = vcat([i for i in range(qntd_n2_real + 1, qntd_n2_candidato + qntd_n2_real)])
S_locais_candidatos_n3 = vcat([i for i in range(qntd_n3_real + 1, qntd_n3_candidato + qntd_n3_real)])


S_n1 = vcat(S_instalacoes_reais_n1, S_locais_candidatos_n1)
S_n2 = vcat(S_instalacoes_reais_n2, S_locais_candidatos_n2)
S_n3 = vcat(S_instalacoes_reais_n3, S_locais_candidatos_n3)
S_Pontos_Demanda = vcat([i for i in range(1, length(df_m.CD_SETOR))])
S_Valor_Demanda = vcat([i for i in values(c_demanda)])



#agora preciso concatenar os dados de distância (latitude, longitude) no mesmo formato dos conjuntos!
#TODO: PASSAR ESSAS COISAS FEITAS 3X PARA MÉTODOS DE CLASSE!
S_Coordenadas_demandas = vcat([i for i in values(c_coords)])
coords_inst_real_n1 = vcat([(df_n1[!, "latitude"][i], df_n1[!, "longitude"][i])  for i in range(1, qntd_n1_real)])
coords_inst_real_n2 = vcat([(df_n2[!, "latitude"][i], df_n2[!, "longitude"][i])  for i in range(1, qntd_n2_real)])
coords_inst_real_n3 = vcat([(df_n3[!, "latitude"][i], df_n3[!, "longitude"][i])  for i in range(1, qntd_n3_real)])

coords_S1 = vcat(coords_inst_real_n1, S_Coordenadas_demandas)
coords_S2 = vcat(coords_inst_real_n2, S_Coordenadas_demandas)
coords_S3 = vcat(coords_inst_real_n3, S_Coordenadas_demandas)


Matriz_Dist_n1 = [haversine([c1[1], c1[2]], [c2[1], c2[2]])/1000 for c1 in S_Coordenadas_demandas , c2 in coords_S1]
Matriz_Dist_n2 = [haversine([c1[1], c1[2]], [c2[1], c2[2]])/1000 for c1 in coords_S1 , c2 in coords_S2]
Matriz_Dist_n3 = [haversine([c1[1], c1[2]], [c2[1], c2[2]])/1000 for c1 in coords_S2 , c2 in coords_S3]
m_aux = [haversine([c1[1], c1[2]], [c2[1], c2[2]])/1000 for c1 in coords_inst_real_n1 , c2 in coords_inst_real_n2]

#Calcular raio via outras metodologias!
Dist_Maxima_Demanda_N1 = 3000/1000
Dist_Maxima_n1_n2 = 10000/1000
Dist_Maxima_n2_n3 = 25000/1000

custo_abertura_nova_instalacao_n1 = 500000
custo_abertura_nova_instalacao_n2 = 1500000
custo_abertura_nova_instalacao_n3 = 5000000

custo_abertura_n1 = vcat(fill(0, qntd_n1_real, 1), fill(custo_abertura_nova_instalacao_n1, qntd_n1_candidato, 1))
custo_abertura_n2 = vcat(fill(0, qntd_n2_real, 1), fill(custo_abertura_nova_instalacao_n2, qntd_n2_candidato, 1))
custo_abertura_n3 = vcat(fill(0, qntd_n3_real, 1), fill(custo_abertura_nova_instalacao_n3, qntd_n3_candidato, 1))

#Criação dos dominios!
dominio_atr_n1 = Dict(d => [n for n in S_n1 if Matriz_Dist_n1[d,n] <= Dist_Maxima_Demanda_N1] for d in S_Pontos_Demanda)
dominio_atr_n2 = Dict(d => [n for n in S_n2 if Matriz_Dist_n2[d,n] <= Dist_Maxima_n1_n2] for d in S_n1)
dominio_atr_n3 = Dict(d => [n for n in S_n3 if Matriz_Dist_n3[d,n] <= Dist_Maxima_n2_n3] for d in S_n2)

#Porcentagens do andamento do fluxo!
percent_n1_n2 = 0.4
percent_n2_n3 = 0.7
S_pacientes = [1,2]

max_abr_n1 = 8
max_abr_n2 = 4
max_abr_n3 = 2

#TODO:
#fluxo n1 binário!
#Capacidades n1 é 1000 pra cronico e agudo!
#Pegar esse dado com ministério da saúde para primário e calcular via numéro de leitos no secundário!
#Para as instalações, considerar que tem convênio SUS!
#Definir abertura de novas unidades capacitadas ou não a depender da rodada do modelo
#Máximo de aberturas de unidades no ano de acordo com abertura de histórica de dados.
#Definir locais candidatos de acordo com definições arbitrarias
    #Ver quais são necessárias para viabilidade e escolher eles!
#Dividir coluna carga_horaria_hospitalar_sus por 170 e e encontro a quantiade de profissionais!
#Proffisionais que cubram pelo menos 80% das instalações (Pareto)
#Salarios do glassdoor ou outro site
#Parametros de saúde: https://saude.campinas.sp.gov.br/programas/protocolos/Parametros_SUS_2015.pdf
#Relatório 


model = JuMP.Model(HiGHS.Optimizer)
set_optimizer_attribute(model, "time_limit", 500.0)
set_optimizer_attribute(model, "primal_feasibility_tolerance", 1e-6)
set_optimizer_attribute(model, "mip_rel_gap", 0.01) 

#Passar pra binário o n1!
fluxo_n1 = @variable(model, X_n1[d in S_Pontos_Demanda, n1 in dominio_atr_n1[d], p in S_pacientes] >= 0) #Usei o indice P aqui para calcular fluxo!
fluxo_n2 = @variable(model, X_n2[n1 in S_n1, n2 in dominio_atr_n2[n1], p in S_pacientes] >= 0)
fluxo_n3 = @variable(model, X_n3[n2 in S_n2, n3 in dominio_atr_n3[n2], p in S_pacientes] >= 0)

var_abr_n1 = @variable(model, Abr_n1[n1 in S_locais_candidatos_n1], Bin)
var_abr_n2 = @variable(model, Abr_n2[n2 in S_locais_candidatos_n2], Bin)
var_abr_n3 = @variable(model, Abr_n3[n3 in S_locais_candidatos_n3], Bin)

#Fluxo equipes
fluxo_eq_n1 = @variable(model, eq_n1[eq in S_equipes, n1 in S_n1])
fluxo_eq_n2 = @variable(model, eq_n2[eq in S_equipes_n2, n1 in S_n2])
fluxo_eq_n3 = @variable(model, eq_n3[eq in S_equipes_n3, n1 in S_n3])


#Restrições fluxo
@constraint(model, [d in S_Pontos_Demanda, p in S_pacientes], S_Valor_Demanda[d] * porcentagem_populacao[p] == sum(X_n1[d, n1, p] for n1 in dominio_atr_n1[d]))
@constraint(model, [n1 in S_n1, p in S_pacientes], sum(X_n2[n1, n2, p] for n2 in dominio_atr_n2[n1]) == percent_n1_n2 * sum(X_n1[d, n1, p] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]) )
@constraint(model, [n2 in S_n2, p in S_pacientes], sum(X_n3[n2, n3, p] for n3 in dominio_atr_n3[n2]) ==  percent_n2_n3 * sum(X_n2[n1, n2, p] for n1 in S_n1 if n2 in dominio_atr_n2[n1]) )


#Restricoes abertura de novas unidades
@constraint(model, [un in S_locais_candidatos_n1], sum(X_n1[d, un, p] for d in S_Pontos_Demanda, p in S_pacientes if un in dominio_atr_n1[d]) <= sum(S_Valor_Demanda[:]) * Abr_n1[un])
@constraint(model, [un in S_locais_candidatos_n2], sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes if un in dominio_atr_n2[n1]) <= sum(S_Valor_Demanda[:]) * Abr_n2[un])
@constraint(model, [un in S_locais_candidatos_n3], sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes if un in dominio_atr_n3[n2]) <= sum(S_Valor_Demanda[:]) * Abr_n3[un])


#Abertura Máxima de novas unidades. #Essas mochilas gigantes vão pesar o modelo!
@constraint(model, sum(Abr_n1[un] for un in S_locais_candidatos_n1) <= max_abr_n1)
@constraint(model, sum(Abr_n2[un] for un in S_locais_candidatos_n2) <= max_abr_n2)
@constraint(model, sum(Abr_n3[un] for un in S_locais_candidatos_n3) <= max_abr_n3)


#Capacidade das Unidades! Não tenho esse dado! Dividir esse dado para cronico e agudo!
#Pegar esse dado com ministério da saúde para primário e calcular via numéro de leitos no secundário!
TESTE_CAP_1 = 10000
TESTE_CAP_2 = 150000
TESTE_CAP_3 = 800000

@constraint(model, [n1 in S_n1, p in S_pacientes], sum(X_n1[d, n1, p] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]) <= TESTE_CAP_1)
@constraint(model, [n2 in S_n2], sum(X_n2[n1,n2, p] for n1 in S_n1, p in S_pacientes if n2 in dominio_atr_n2[n1]) <= TESTE_CAP_2)
@constraint(model, [n3 in S_n3], sum(X_n3[n2, n3, p] for n2 in S_n2, p in S_pacientes if n3 in dominio_atr_n3[n2]) <= TESTE_CAP_3)

#Capacidade das equipes
#Bases que não existem tem profissionais???

@constraint(model, [eq in S_equipes, un in S_instalacoes_reais_n1], 
            qntd_equipes_por_n1[un, eq] + fluxo_eq_n1[eq,un] == sum(X_n1[d, un, p] for d in S_Pontos_Demanda, p in S_pacientes if un in dominio_atr_n1[d]) * capacidade_maxima_por_equipe_n1[eq])


@constraint(model, [eq in S_equipes, un in S_locais_candidatos_n1], 
           fluxo_eq_n1[eq,un] == sum(X_n1[d, un, p] for d in S_Pontos_Demanda, p in S_pacientes if un in dominio_atr_n1[d]) * capacidade_maxima_por_equipe_n1[eq])



@constraint(model, [eq in S_equipes_n2, un in S_instalacoes_reais_n2], 
        S_capacidade_CNES_n2[un, eq] + fluxo_eq_n2[eq,un] == sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes if un in dominio_atr_n2[n1]) * S_eq_por_paciente_n2[eq])


@constraint(model, [eq in S_equipes_n2, un in S_locais_candidatos_n2], 
         fluxo_eq_n2[eq,un] == sum(X_n2[n1, un, p] for n1 in S_n1, p in S_pacientes if un in dominio_atr_n2[n1]) * S_eq_por_paciente_n2[eq])


@constraint(model, [eq in S_equipes_n3, un in S_instalacoes_reais_n3], 
         S_capacidade_CNES_n3[un, eq] + fluxo_eq_n3[eq,un] == sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes if un in dominio_atr_n3[n2]) * S_eq_por_paciente_n3[eq])



@constraint(model, [eq in S_equipes_n3, un in S_locais_candidatos_n3],
        fluxo_eq_n3[eq,un] == sum(X_n3[n2, un, p] for n2 in S_n2, p in S_pacientes if un in dominio_atr_n3[n2]) * S_eq_por_paciente_n3[eq])


custo_deslocamento = 5
Custo_abertura_n1 = 100000
S_custo_fixo_n1 = 10000
S_custo_equipe_n1 = 100
S_custo_variavel_n1 = [200, 100]


S_custo_fixo_n2 = 100000
S_custo_equipe_n2 = 1000
S_custo_variavel_n2 = [400, 200]

S_custo_fixo_n3 = 500000
S_custo_equipe_n3 = 5000
S_custo_variavel_n3 = [1000, 600]

@expression(model, custo_logistico_n1,  sum(X_n1[d, un, p] * Matriz_Dist_n1[d, un] * custo_deslocamento for d in S_Pontos_Demanda, un in S_n1, p in S_pacientes if un in dominio_atr_n1[d]))
@expression(model, custo_fixo_novos_n1, sum(Abr_n1[un] * Custo_abertura_n1 for un in S_locais_candidatos_n1))
@expression(model, custo_fixo_existente_n1, sum(S_custo_fixo_n1 for un1 in S_instalacoes_reais_n1))
@expression(model, custo_times_novos_n1, sum(fluxo_eq_n1[eq, un] * S_custo_equipe_n1 for eq in S_equipes, un in S_n1))
@expression(model, custo_variavel_n1, sum(X_n1[d, un, p] * S_custo_variavel_n1[p] for d in S_Pontos_Demanda, un in S_n1, p in S_pacientes if un in dominio_atr_n1[d]))

@expression(model, custo_logistico_n2,  sum(X_n2[un, un2, p] * Matriz_Dist_n2[un, un2] * custo_deslocamento for un2 in S_n2, un in S_n1, p in S_pacientes if un2 in dominio_atr_n2[un]))
@expression(model, custo_fixo_novos_n2, sum(Abr_n2[un] * S_custo_fixo_n2 for un in S_locais_candidatos_n2))
@expression(model, custo_fixo_existente_n2, sum(S_custo_fixo_n2 for un2 in S_instalacoes_reais_n2))
@expression(model, custo_times_novos_n2, sum(fluxo_eq_n2[eq, un] * S_custo_equipe_n2 for eq in S_equipes_n2, un in S_n2))
@expression(model, custo_variavel_n2, sum(X_n2[un,un2, p] * S_custo_variavel_n2[p] for un2 in S_n2, un in S_n1, p in S_pacientes if un2 in dominio_atr_n2[un]))


@expression(model, custo_logistico_n3,  sum(X_n3[un2, un3, p] * Matriz_Dist_n3[un2, un3] * custo_deslocamento for un2 in S_n2, un3 in S_n3, p in S_pacientes if un3 in dominio_atr_n2[un2]))
@expression(model, custo_fixo_novos_n3, sum(Abr_n3[un] * S_custo_fixo_n3 for un in S_locais_candidatos_n3))
@expression(model, custo_fixo_existente_n3, sum(S_custo_fixo_n3 for un3 in S_instalacoes_reais_n3))
@expression(model, custo_times_novos_n3, sum(fluxo_eq_n3[eq, un] * S_custo_equipe_n3 for eq in S_equipes_n3, un in S_n3))
@expression(model, custo_variavel_n3, sum(X_n3[un2,un3, p] * S_custo_variavel_n3[p] for un2 in S_n2, un3 in S_n3, p in S_pacientes if un3 in dominio_atr_n2[un2]))


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
for d in S_Pontos_Demanda
    v = sum(value(X_n1[d,n,p]) for n in S_n1, p in S_pacientes if n in dominio_atr_n1[d])
    println(string("Demanda ", d, " Valor ", v))
end



println("=========================================================")
println("Fluxo Nível primário")

for d in S_Pontos_Demanda, un in S_n1, p in S_pacientes
    if un in dominio_atr_n1[d]
        if value(fluxo_n1[d,un,p]) == 0
            continue
        end
        println(string("Origem: ", d, ", Destino: ", un ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n1[d,un,p]) ))
end
end

println("=========================================================")
println("Fluxo Nível Secundário")

for un in S_n1, un2 in S_n2, p in S_pacientes
    if un2 in dominio_atr_n2[un]
    if value(fluxo_n2[un,un2,p]) <= 0.1
        continue
    end
    println(string("Origem: ", un, ", Destino: ", un2 ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n2[un,un2,p]) ))
end
end

println("=========================================================")
println("Fluxo Nível Terciario")
for un2 in S_n2, un3 in S_n3,p in S_pacientes
    if un3 in dominio_atr_n3[un2]
        if value(fluxo_n3[un2,un3, p]) == 0
            continue
        end
        println(string("Origem: ", un2, ", Destino: ", un3 ,  ", Tipo: ", p ,", Valor: ", value(fluxo_n3[un2,un3, p]) ))
    end
end


print("=========================================================")
println("Fluxo Equipes Primário")

for n in S_n1, eq in S_equipes
    if value(fluxo_eq_n1[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n1[eq, n]) ))
end


println("=========================================================")
println("Fluxo Equipes Secundário")

for n in S_n2, eq in S_equipes_n2
    if value(fluxo_eq_n2[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n2[eq, n]) ))
end


println("=========================================================")
println("Fluxo Equipes Terciário")

for n in S_n3, eq in S_equipes_n3
    if value(fluxo_eq_n3[eq, n]) == 0
        continue
    end
    println(string("Equipe: ", eq, ", Instalacao: ", n ,  ", Fluxo: ", value(fluxo_eq_n3[eq, n]) ))
end



println("=========================================================")
println("Capacidades usadas N1")

for n in S_n1
    if (n in dominio_atr_n1[d]) && (value(X_n1[d,n,p]) > 0)
    v = sum(value(X_n1[d,n,p]) for d in S_Pontos_Demanda, p in S_pacientes)
    println(string("Facility ", n, " Valor ", v))
    end
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


