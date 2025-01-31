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
municipio = "Contagem"
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

lista_equipes_n2 = ["Porte 1", "Porte 2", "Porte 3"]
qntd_equipes_n2 = length(lista_equipes_n2)
S_equipes_n2 = vcat([i for i in range(1, qntd_equipes_n2)])
#Dados aqui vão ser de capacidade!
capacidade_maxima_por_equipe_n2 = vcat([100000, 200000, 300000]) 
S_porte_instalacao_real_n2 = vcat([capacidade_maxima_por_equipe_n2[i] for i in df_n2[!,"classificacao_Sec"]])


############### NÍVEL Terciário ###############
lista_equipes_n3 = ["Cardio", "Neuro", "Espec1", "Espec2", "Espec3", "Espec4", "Espec5"]
qntd_equipes_n3 = length(lista_equipes_n3)
S_equipes_n3 = vcat([i for i in range(1, qntd_equipes_n3)])
capacidade_maxima_por_equipe_n3 = vcat([1/10000, 1/20000, 1/5000, 1/1800, 1/1000, 1/12000, 1/13000])


lista_doencas = ["Crônico", "Agudo"]
porcentagem_populacao = [0.8, 0.2] #Ponderar demanda?


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
percent_n1_n2 = 1
percent_n2_n3 = 1


# Inicialmente irei fazer 2 rodadas para estudo.
# 1: Rodada sem fixar a capacidade das instalações secundárias para verificar se apenas redistribuindo (sem abrir novas unidades) eu consigo atender as capacidades. Impedir a abertura de novas unidades n2
fixa_secundarias = false
fixa_instalacoes_primarias = false
fixa_equipes_primarias = false
fixa_referencia_CS_UBS = false


model = JuMP.Model(HiGHS.Optimizer)
set_optimizer_attribute(model, "time_limit", 1500.0)
set_optimizer_attribute(model, "primal_feasibility_tolerance", 1e-6)
set_optimizer_attribute(model, "mip_rel_gap", 0.01) 




#Variaveis de fluxo!!
if fixa_referencia_CS_UBS
    var_atr_demanda_n1 = @variable(model, atr_n1[d in S_Pontos_Demanda, n1 in S_n1] >= 0) #Resolver problema dos dados dos CS sem UBS relacionada! Ver porque UPA Inconfidentes está saindo dos filtros!
    @constraint(model, [d in S_Pontos_Demanda], atr_n1[d, S_relacao_UBS_SC[d]] == S_Valor_Demanda[d])
    fixa_instalacoes_primarias = true
    @expression(model, custo_social_n1, sum(atr_n1[d,n1] * Matriz_Dist_n1[d,n1] for d in S_Pontos_Demanda, n1 in dominio_atr_n1[d]))

    
else
    var_atr_demanda_n1 = @variable(model, atr_n1[d in S_Pontos_Demanda, n1 in dominio_atr_n1[d]] >= 0)
    @expression(model, custo_social_n1, sum(atr_n1[d,n1] * Matriz_Dist_n1[d,n1] for d in S_Pontos_Demanda, n1 in dominio_atr_n1[d]))
end

var_atr_n1_n2 = @variable(model, atr_n2[i in S_n1, j in dominio_atr_n2[i]] >= 0)
var_atr_n2_n3 = @variable(model, atr_n3[i in S_n2, j in dominio_atr_n3[i]] >= 0)

#variaveis de abertura - Manutenção dos locais já abertos!
var_abr_n1 = @variable(model, abr_n1[n1 in S_locais_candidatos_n1], Bin)
var_abr_n2 = @variable(model, abr_n2[n2 in S_locais_candidatos_n2], Bin)
var_abr_n3 = @variable(model, abr_n3[n3 in S_locais_candidatos_n3], Bin)


#Variáveis de capacidade!
#n1 por equipes inicialmente!
qntd_eq_n1 = @variable(model, qntd_eq_n1[S_n1, S_equipes] >= 0) 
qntd_eq_n3 = @variable(model, qntd_eq_n3[S_n3, S_equipes_n3] >= 0)


#Restrições fluxo Demanda - n1
#toda demanda precisa ser atendida!
if fixa_instalacoes_primarias == true
    var_atr_demanda_n1_folga = @variable(model, atr_n1_folga[d in S_Pontos_Demanda, n1 in S_n1] >= 0) 
    @constraint(model, [d in S_Pontos_Demanda], sum(atr_n1[d,n1] for n1 in dominio_atr_n1[d] if n1 in S_instalacoes_reais_n1) 
                                              + sum(atr_n1_folga[d,n1] for n1 in S_n1)  #Dá pra tratar casos de pontos de demanda sem local real no pós-processamento. Tirar isso do modelo!
                                                == S_Valor_Demanda[d])

    @expression(model, custo_abertura_n1_FO, sum(atr_n1_folga[d, n1] * 10000 for d in S_Pontos_Demanda, n1 in S_n1))                                            
else
    @constraint(model, [d in S_Pontos_Demanda], sum(atr_n1[d,n1] for n1 in dominio_atr_n1[d]) == S_Valor_Demanda[d])
    @constraint(model, [n1_c in S_locais_candidatos_n1], sum(atr_n1[d, n1_c] for d in S_Pontos_Demanda if n1_c in dominio_atr_n1[d]) <= abr_n1[n1_c] * 1000000)
    @expression(model, custo_abertura_n1_FO, sum(var_abr_n1[n1] * custo_abertura_n1[n1] for n1 in S_locais_candidatos_n1))
end



if fixa_equipes_primarias == true
    #Posso ter necessidade de folgas!
    qntd_eq_n1_folga = @variable(model, qntd_eq_n1_folga[S_instalacoes_reais_n1, S_n1] >= 0)
    @constraint(model, [n1 in S_instalacoes_reais_n1, eq in S_equipes], sum(atr_n1[d, n1] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]) <= # E se eu fixar a relação e o atendimento não for no raio de ação?
                                        pop_maxima_por_equipe_n1[eq] * qntd_equipes_por_n1[n1, eq] + qntd_eq_n1_folga[n1, eq]) 
    
    @expression(model, custo_equipes_n1, sum(qntd_eq_n1_folga[n1, eq] * 100000 for n1 in S_instalacoes_reais_n1, eq in S_equipes))
else
    @constraint(model, [n1 in S_n1, eq in S_equipes], sum(atr_n1[d, n1] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]) 
    * capacidade_maxima_por_equipe_n1[eq] == qntd_eq_n1[n1, eq])
    @expression(model, custo_equipes_n1, sum(qntd_eq_n1[n1, eq] * 1000 for n1 in S_n1, eq in S_equipes))

end



@expression(model, custo_n1, custo_social_n1 + custo_abertura_n1_FO + custo_equipes_n1)


#Restrições fluxo n1 - n2

if fixa_secundarias == true

    var_folga_demanda_n1_n2 = @variable(model, folga_atr_n2[i in S_n1, j in dominio_atr_n2[i]] >= 0)
    var_folga_eq_n2 = @variable(model, folga_eq_n2[S_n2, S_equipes_n2] >= 0)
    @constraint(model, [n1 in S_n1], sum(atr_n2[n1,n2] for n2 in dominio_atr_n2[n1] if n2 in S_instalacoes_reais_n2) + sum(folga_atr_n2[n1,n2] for n2 in dominio_atr_n2[n1] if n2 in S_instalacoes_reais_n2)
                                    == percent_n1_n2 * sum(atr_n1[d, n1] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]))

    
                                    
    #Limitador de atendimentos reais!
    @constraint(model, [n2 in S_instalacoes_reais_n2, eq in S_equipes_n2], sum(atr_n2[n1,n2] for n1 in S_n1 if n2 in dominio_atr_n2[n1]) <= S_porte_instalacao_real_n2[n2] + folga_eq_n2[n2, eq])
    
    
    
    @expression(model, custo_folgas, sum(folga_eq_n2[n2, eq] * 10000 for n2 in S_n2, eq in S_equipes_n2) + sum(folga_atr_n2[n1,n2] * 10000 for n1 in S_n1, n2 in dominio_atr_n2[n1]))  #Custo alto para só usar a folga em casos extritamente necessários
    @expression(model, custo_social_n2, sum(atr_n2[n1,n2] * Matriz_Dist_n2[n1,n2] for n1 in S_n1, n2 in dominio_atr_n2[n1]))
    
    @expression(model, custo_n2, custo_folgas + custo_social_n2)

else
    #Se não tiver capacidade, deixar livre para modelo alocar e definir o porte da UPA no pós-processamento
    #Fluxo possibilitando abertura de novos pontos n2
    @constraint(model, [n1 in S_n1], sum(atr_n2[n1,n2] for n2 in dominio_atr_n2[n1]) == percent_n1_n2 * sum(atr_n1[d, n1] for d in S_Pontos_Demanda if n1 in dominio_atr_n1[d]))

    #Abertura locais candidatos
    @constraint(model, [n2_c in S_locais_candidatos_n2], sum(atr_n2[n1,n2_c] for n1 in S_n1 if n2_c in dominio_atr_n2[n1] ) <= abr_n2[n2_c] * 1000000)

    #Custos nivel 2!
    @expression(model, custo_social_n2, sum(atr_n2[n1,n2] * Matriz_Dist_n2[n1,n2] for n1 in S_n1, n2 in dominio_atr_n2[n1]))
    @expression(model, custo_abertura_FO_n2, sum(var_abr_n2[n2] * custo_abertura_n2[n2] for n2 in S_locais_candidatos_n2))

    @expression(model, custo_n2,  custo_social_n2 + custo_abertura_FO_n2)
    
end


#Restricoes fluxo n2 - n3
@constraint(model, [n2 in S_n2], sum(atr_n3[n2,n3] for n3 in dominio_atr_n3[n2]) == percent_n2_n3 * sum(atr_n2[n1,n2] for n1 in S_n1 if n2 in dominio_atr_n2[n1]))


#Abertura locais candidatos
@constraint(model, [n3_c in S_locais_candidatos_n3], sum(atr_n3[n2,n3_c] for n2 in S_n2) <= abr_n3[n3_c] * 100000)


@constraint(model, [n3 in S_n3, eq in S_equipes_n3], sum(atr_n3[n2,n3] for n2 in S_n2) * capacidade_maxima_por_equipe_n3[eq] == qntd_eq_n3[n3, eq])

#Custos N3
@expression(model, custo_social_n3, sum(atr_n3[n2,n3] * Matriz_Dist_n3[n2,n3] for n2 in S_n2, n3 in S_n3))
@expression(model, custo_abertura_n3_FO, sum(var_abr_n3[n3] * custo_abertura_n3[n3] for n3 in S_locais_candidatos_n3))
@expression(model, custo_equipes_n3, sum(qntd_eq_n3[n3, eq] * 1000 for n3 in S_n3, eq in S_equipes_n3))
@expression(model, custo_n3, custo_social_n3 + custo_abertura_n3_FO)


#Função Objetivo!
@objective(model, Min, custo_n1 + custo_n2 + custo_n3)

optimize!(model)
obj = objective_value(model)


#Pós-Otimização:
#Instalações candidatas abertas - Não vai abrir nenhuma porque é muito caro!
bases_abertas_n1 = [(v, value(v)) for v in var_abr_n1 if value(v) > 0]
bases_abertas_n2 = [(v, value(v)) for v in var_abr_n2 if value(v) > 0]
bases_abertas_n3 = [(v, value(v)) for v in var_abr_n3 if value(v) > 0]


#Fluxos de demanda - Demanda n1 é distribuida, mas n2 e n3 vão para a instalação mais próxima!
fluxos_abertos_n1 = [(v, value(v)) for v in var_atr_demanda_n1 if value(v) > 0]
fluxos_abertos_n2 = [(v, value(v)) for v in var_atr_n1_n2 if value(v) > 0]
fluxos_abertos_n3 = [(v, value(v)) for v in var_atr_n2_n3 if value(v) > 0]


fluxos_por_unidade_secundaria = Dict(un => sum([value(v) for v in var_atr_n1_n2[:, un] if value(v) > 0]) for un in S_instalacoes_reais_n2)
Dict(x => 0 for x in S_instalacoes_reais_n2)


if fixa_secundarias == true
    uso_folgas_eq_n2 = Dict(un => [value(v) for v in var_atr_n1_n2[:, un] if value(v) > 0] for un in S_instalacoes_reais_n2) #Vai indicar nessecidade ou excesso de leitos!
    uso_folga_demanda_n2 = [(v, value(v)) for v in var_folga_demanda_n1_n2 if value(v) > 0] #Indicar acessibilidade de raio!

else
    equipes_abertas_n2 = [(v, value(v)) for v in qntd_eq_n2 if value(v) > 0]
end





equipes_abertas_n1 = [(v, value(v)) for v in qntd_eq_n1 if value(v) > 0]
equipes_abertas_n3 = [(v, value(v)) for v in qntd_eq_n3 if value(v) > 0]


#Vai indicar se precisa de aumento de capacidade para manter viabilidade no raio!




[(v, value(v)) for v in var_atr_demanda_n1[:, 293] if value(v) > 0]


#Resultado esperado: atribuições para menor distância criando as quantidades de equipes ponderadas!