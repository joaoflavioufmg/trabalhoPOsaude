import json
from geopy.distance import geodesic
# from shapely.geometry import shape
import pandas as pd
from shapely.wkt import loads

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_centroid(geometry):
    geom = loads(geometry)
    centroid = geom.centroid
    return centroid.y, centroid.x

def calculate_distance(demand_coords, supply_coords):
    return round(geodesic(demand_coords, supply_coords).kilometers, 3)

def calculate_distance_matrix_demand_to_level(demand_data, level_data):
    matrix = {}
    for demand in demand_data:
        demand_id = demand['NOME']#demand['ID_BAIRRO']
        demand_coords = get_centroid(demand['GEOMETRIA'])
        matrix[demand_id] = {}
        for supply in level_data:
            supply_id = supply['name']
            supply_coords = (supply['latitude'], supply['longitude'])
            distance = calculate_distance(demand_coords, supply_coords)
            matrix[demand_id][supply_id] = distance
    return matrix

def calculate_distance_matrix_level_to_level(level_data_1, level_data_2):
    matrix = {}
    for level_1 in level_data_1:
        level_1_id = level_1['name']
        level_1_coords = (level_1['latitude'], level_1['longitude'])
        matrix[level_1_id] = {}
        for level_2 in level_data_2:
            level_2_id = level_2['name']
            level_2_coords = (level_2['latitude'], level_2['longitude'])
            distance = calculate_distance(level_1_coords, level_2_coords)
            matrix[level_1_id][level_2_id] = distance
    return matrix

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    demand_file = "P.O Saude/dados_json/bairro_demanda_set.json"  # Replace with your demand JSON file path
    level_1_file = "P.O Saude/dados_json/EL_1.json"  # Replace with your level 1 JSON file path
    level_2_file = "P.O Saude/dados_json/EL_2.json"  # Replace with your level 2 JSON file path
    level_3_file = "P.O Saude/dados_json/EL_3.json"  # Replace with your level 3 JSON file path
    newLevel1 = "P.O Saude/dados_json/novas_unidades_nivel_1.json"  # Replace with your new unit JSON file path
    newLevel2 = "P.O Saude/dados_json/novas_unidades_nivel_2.json"  # Replace with your new unit JSON file path
    newLevel3 = "P.O Saude/dados_json/novas_unidades_nivel_3.json"  # Replace with your new unit JSON file path
    demand_data = load_json(demand_file)
    level_1_data = load_json(level_1_file)
    level_2_data = load_json(level_2_file)
    level_3_data = load_json(level_3_file)
    new_level_1_data = load_json(newLevel1)
    new_level_2_data = load_json(newLevel2)
    new_level_3_data = load_json(newLevel3)
    print("Calculando matriz de distância para demanda e nível 1")
    distance_matrix_1 = calculate_distance_matrix_demand_to_level(demand_data, level_1_data + new_level_1_data)
    print("Calculando matriz de distância para nível 1 e nível 2")
    distance_matrix_2 = calculate_distance_matrix_level_to_level(level_1_data + new_level_1_data, level_2_data + new_level_2_data)
    print("Calculando matriz de distância para nível 2 e nível 3")
    distance_matrix_3 = calculate_distance_matrix_level_to_level(level_2_data + new_level_2_data, level_3_data + new_level_3_data)

    save_json(distance_matrix_1, 'P.O Saude/dados_json/distance_matrix_1.json')
    save_json(distance_matrix_2, 'P.O Saude/dados_json/distance_matrix_2.json')
    save_json(distance_matrix_3, 'P.O Saude/dados_json/distance_matrix_3.json')



