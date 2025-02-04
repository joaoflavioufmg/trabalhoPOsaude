import pandas as pd
import json

def process_professionals(professionals_csv, el_json, output_json, cnes_output_json, include_cbo):
    # Load the professionals CSV file with specified dtype
    dtype = {
        'NOME': str, 'CNS': str, 'SEXO': str, 'IBGE': str, 'UF': str, 'MUNICIPIO': str,
        'CBO': str, 'DESCRICAO CBO': str, 'CNES': str, 'CNPJ': str, 'ESTABELECIMENTO': str,
        'NATUREZA JURIDICA': str, 'DESCRICAO NATUREZA JURIDICA': str, 'GESTAO': str, 'SUS': str,
        'RESIDENTE': str, 'PRECEPTOR': str, 'VINCULO ESTABELECIMENTO': str, 'VINCULO EMPREGADOR': str,
        'DETALHAMENTO DO VINCULO': str, 'CH OUTROS': float, 'CH AMB.': float, 'CH HOSP.': float
    }
    df = pd.read_csv(professionals_csv, delimiter=';', dtype=dtype)

    # Load the EL JSON file
    with open(el_json, 'r', encoding='utf-8') as file:
        el_data = json.load(file)

    # Get the list of hospital IDs from the EL data
    hospital_ids = [el['name'] for el in el_data]

    # Filter professionals by SUS and those working in the hospitals
    df_sus = df[(df['SUS'] == 'S') & (df['ESTABELECIMENTO'].isin(hospital_ids))]

    # Include only professionals with certain DESCRICAO CBO values
    df_sus = df_sus[df_sus['DESCRICAO CBO'].isin(include_cbo)]

    # Aggregate information
    descricao_cbo_freq = df_sus['DESCRICAO CBO'].value_counts().to_dict()
    custo_cbo = df_sus.groupby('DESCRICAO CBO')['CH HOSP.'].apply(lambda x: (x * 10).sum()).to_dict()  # Example cost calculation

    # Apply Pareto principle to include only the top 80% of frequencies
    aggregated_data = {
        'descricao_cbo': {},
        'custo_cbo': {}
    }
    total_freq = sum(descricao_cbo_freq.values())
    cumulative_freq = 0
    for cbo, freq in descricao_cbo_freq.items():
        if cumulative_freq / total_freq <= 0.8:#pareto
            aggregated_data['descricao_cbo'][cbo] = freq
            aggregated_data['custo_cbo'][cbo] = custo_cbo[cbo]
            cumulative_freq += freq
        else:
            break

    # Save the aggregated data to the output JSON file
    with open(output_json, 'w', encoding='utf-8') as file:
        json.dump(aggregated_data, file, ensure_ascii=False, indent=4)

    # Load the aggregated data to get the list of relevant CBO categories
    with open(output_json, 'r', encoding='utf-8') as file:
        equipe_data = json.load(file)

    relevant_cbo = set(equipe_data['descricao_cbo'].keys())

    # Create CNES data for professionals in the filtered SUS dataframe
    cnes_data = {}
    for el in el_data:
        cnes = el['name']
        cnes_data[cnes] = {cbo: 0 for cbo in relevant_cbo}  # Initialize with all relevant CBOs
        for _, row in df_sus[df_sus['ESTABELECIMENTO'] == cnes].iterrows():
            cbo_description = row['DESCRICAO CBO']
            if cbo_description in relevant_cbo:
                cnes_data[cnes][cbo_description] += 1

    # Save the CNES data to the CNES output JSON file
    with open(cnes_output_json, 'w', encoding='utf-8') as file:
        json.dump(cnes_data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__": 
    levels = ['1', '2', '3']
    include_cbo = [
        "FONOAUDIOLOGO EM AUDIOLOGIA",
        "PROFISSIONAL DE EDUCACAO FISICA NA SAUDE",
        "AUXILIAR TECNICO EM LABORATORIO DE FARMACIA",
        "TECNICO DE ENFERMAGEM",
        "TECNICO DE ENFERMAGEM DE TERAPIA INTENSIVA",
        "TECNICO DE ENFERMAGEM DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "TECNICO EM SAUDE BUCAL DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "TECNOLOGO EM RADIOLOGIA",
        "COMUNITARIO DE SAUDE",
        "ENFERMEIRO",
        "ENFERMEIRO AUDITOR",
        "ENFERMEIRO PSIQUIATRICO",
        "ENFERMEIRO DO TRABALHO",
        "ENFERMEIRO NEFROLOGISTA",
        "ENFERMEIRO DE CENTRO CIRURGICO",
        "ENFERMEIRO DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "AUXILIAR DE ENFERMAGEM",
        "AUXILIAR DE ENFERMAGEM DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "AGENTE DE COMBATE AS ENDEMIAS",
        "PSICOLOGO CLINICO",
        "ASSISTENTE SOCIAL",#incluir?
        "FISIOTERAPEUTA GERAL",
        "GERENTE DE SERVICOS DE SAUDE",
        "DOSIMETRISTA CLINICO",
        "AUXILIAR EM SAUDE BUCAL DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "NUTRICIONISTA",
        "FARMACEUTICO HOSPITALAR E CLINICO",
        "FONOAUDIOLOGO GERAL",
        "AGENTE DE SAUDE PUBLICA",
        "TECNICO EM FARMACIA",
        "TERAPEUTA OCUPACIONAL",
        "CIRURGIAO DENTISTA  CLINICO GERAL",
        "TECNICO EM SAUDE BUCAL",
        "TRABALHADOR DE SERVICOS DE LIMPEZA E CONSERVACAO DE AREAS PUBLICAS",
        "FISICO (MEDICINA)",
        "FISIOTERAPEUTA RESPIRATORIA",
        "FISIOTERAPEUTA DO TRABALHO",
        "FISIOTERAPEUTA NEUROFUNCIONAL",
        "PROFISSIONAL DE EDUCACAO FISICA NA SAUDE",
        "TECNICO EM PATOLOGIA CLINICA",
        "CIRURGIAO DENTISTA  DENTISTICA",
        "CIRURGIAO DENTISTA  PROTESISTA",
        "CIRURGIAO DENTISTA  ENDODONTISTA",
        "CIRURGIAO DENTISTA  RADIOLOGISTA",
        "CIRURGIAO DENTISTA  PERIODONTISTA",
        "CIRURGIAO DENTISTA  ODONTOPEDIATRA",
        "CIRURGIAO DENTISTA  ESTOMATOLOGISTA",
        "CIRURGIAO DENTISTA  IMPLANTODONTISTA",
        "CIRURGIAO DENTISTA  PATOLOGISTA BUCAL",
        "CIRURGIAO DENTISTA  ODONTOLOGISTA LEGAL",
        "CIRURGIAO DENTISTA  ORTOPEDISTA E ORTODONTISTA",
        "CIRURGIAO DENTISTA  PROTESIOLOGO BUCOMAXILOFACIAL",
        "CIRURGIAO DENTISTA  TRAUMATOLOGISTA BUCOMAXILOFACIAL",
        "CIRURGIAO DENTISTA  DISFUNCAO TEMPOROMANDIBULAR E DOR OROFACIAL",
        "CIRURGIAO DENTISTA  ODONTOLOGIA PARA PACIENTES COM NECESSIDADES ESPECIAIS",
        "CIRURGIAODENTISTA DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "ENFERMEIRO OBSTETRICO",
        "BIOLOGO",
        "FARMACEUTICO",
        "AUXILIAR EM SAUDE BUCAL",
        "TECNICO DE ORTOPEDIA",
        "TECNICO EM RADIOLOGIA E IMAGENOLOGIA",
        "TECNICO DE ENFERMAGEM DO TRABALHO",
        "TECNICO EM NUTRICAO E DIETETICA",
        "TECNICO EM LABORATORIO DE FARMACIA",
        "AGENTE DE ACAO SOCIAL",#incluir?
        "BIOMEDICO",
        "FARMACEUTICO ANALISTA CLINICO",
        "ENFERMEIRO NEONATOLOGISTA",
        "ENFERMEIRO DE TERAPIA INTENSIVA",
        "PSICOLOGO HOSPITALAR",
        "AVALIADOR FISICO",
        "AUXILIAR DE LABORATORIO DE ANALISES FISICOQUIMICAS",
        "AUXILIAR DE LABORATORIO DE ANALISES CLINICAS",
        "AUXILIAR DE RADIOLOGIA (REVELACAO FOTOGRAFICA)",
        "FONOAUDIOLOGO EM VOZ",
        "PSICOLOGO SOCIAL",
        "PSICOLOGO DO TRABALHO",
        "MEDICO RESIDENTE",
        "MEDICO HEMATOLOGISTA",
        "MEDICO ACUPUNTURISTA",
        "MEDICO HOMEOPATA",
        "MEDICO PSIQUIATRA",
        "MEDICO EM MEDICINA INTENSIVA",
        "MEDICO GENERALISTA",
        "MEDICO CIRURGIAO PEDIATRICO",
        "MEDICO CLINICO",
        "MEDICO CARDIOLOGISTA",
        "MEDICO PNEUMOLOGISTA",
        "MEDICO GENETICISTA",
        "MEDICO GASTROENTEROLOGISTA",
        "MEDICO DA ESTRATEGIA DE SAUDE DA FAMILIA",
        "MEDICO DE FAMILIA E COMUNIDADE",
        "MEDICO EM RADIOLOGIA E DIAGNOSTICO POR IMAGEM",
        "MEDICO CIRURGIAO CARDIOVASCULAR",
        "MEDICO NEUROLOGISTA",
        "MEDICO ENDOCRINOLOGISTA E METABOLOGISTA",
        "MEDICO INFECTOLOGISTA",
        "MEDICO ANESTESIOLOGISTA",
        "MEDICO EM ENDOSCOPIA",
        "MEDICO CIRURGIAO GERAL",
        "MEDICO UROLOGISTA",
        "MEDICO MASTOLOGISTA",
        "MEDICO DERMATOLOGISTA",
        "MEDICO PEDIATRA",
        "MEDICO OFTALMOLOGISTA",
        "MEDICO REUMATOLOGISTA",
        "MEDICO NUTROLOGISTA",
        "MEDICO NEUROCIRURGIAO"
        "MEDICO NEFROLOGISTA",
        "MEDICO ORTOPEDISTA E TRAUMATOLOGISTA",
        "MEDICO COLOPROCTOLOGISTA",
        "MEDICO ANGIOLOGISTA",
        "MEDICO CIRURGIAO PLASTICO",
        "MEDICO GINECOLOGISTA E OBSTETRA",
        "MEDICO OTORRINOLARINGOLOGISTA",
        "MEDICO CIRURGIAO DE CABECA E PESCOCO",
        "MEDICO EM CIRURGIA VASCULAR",
        "MEDICO FISIATRA",
        "MEDICO DO TRABALHO"
        "MEDICO ONCOLOGISTA CLINICO",
        "MEDICO CANCEROLOGISTA CIRURGICO",
        "MEDICO CIRURGIAO TORACICO",
        "MEDICO CIRURGIAO DO APARELHO DIGESTIVO",
        "MEDICO CARDIOLOGISTA INTERVENCIONISTA",
        "MEDICO GERIATRA",
        "MEDICO EM MEDICINA NUCLEAR",
        "MEDICO RADIOTERAPEUTA",
        "MEDICO HEMOTERAPEUTA",
        "MEDICO CANCEROLOGISTA PEDIATRICO",
        "MEDICO PATOLOGISTA",
        "MEDICO PATOLOGISTA CLINICO  MEDICINA LABORATORIAL",
        "MEDICO ANATOMOPATOLOGISTA",
        "MEDICO CIRURGIAO DA MAO",
        "MEDICO RADIOLOGISTA INTERVENCIONISTA",
        "MEDICO NEUROFISIOLOGISTA CLINICO",
        "MEDICO ALERGISTA E IMUNOLOGISTA",
        "MEDICO CITOPATOLOGISTA",
        "MEDICO EM MEDICINA PREVENTIVA E SOCIAL",
        "MEDICO SANITARISTA",
        "DIETISTA"
        "ORTOPTISTA",
        "CUIDADOR EM SAUDE",
        "MEDICO HOMEOPATA",#isso não é medico e nem devia ta aq
        "TECNICO EM HEMOTERAPIA",# Mais homeopatia??????????????/
        "NEUROPSICOLOGO",
        "CUIDADOR DE IDOSOS"
        ]

    for level in levels:
        professionals_csv = f'P.O Saude/data_excel/profissionais-310620.csv'  # Replace with your professionals CSV file path
        el_json = f'P.O Saude/dados_json/EL_{level}.json'  # Replace with your EL JSON file path
        output_json = f'P.O Saude/dados_json/Equipe_{level}.json'  # Replace with your output JSON file path
        cnes_output_json = f'P.O Saude/dados_json/CNES_{level}.json'  # Replace with your CNES output JSON file path

        process_professionals(professionals_csv, el_json, output_json, cnes_output_json, include_cbo)
