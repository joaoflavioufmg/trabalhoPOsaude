# import csv
import json
import geopandas as gpd
from shapely import wkt
import pandas as pd

def read_xlsx_and_generate_json(input_xlsx, output_json):
    data = []

    df = pd.read_excel(input_xlsx)
    for _, row in df.iterrows():
        if row['municipio_nome'] != 'BELO HORIZONTE':
            continue

        data.append({
            "name": row['nome_fantasia'],
            "id": str(row['instalacao_codigo']) + " " + row['nome_fantasia'],
            "location": row['location'],
            "latitude": row['latitude'],
            "longitude": row['longitude'],
            "type": row['tipo_estabelecimento']
        })

    with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_files = [
        'data_excel/instalacoes_primarias.xlsx',  # Replace with your XLSX file paths
        'data_excel/instalacoes_secundarias.xlsx',
        'data_excel/instalacoes_terciarias.xlsx'
    ]
    output_files = [
        'dados_json/EL_1.json',
        'dados_json/EL_2.json',
        'dados_json/EL_3.json'
    ]

    for input_xlsx, output_json in zip(input_files, output_files):
        read_xlsx_and_generate_json(input_xlsx, output_json)