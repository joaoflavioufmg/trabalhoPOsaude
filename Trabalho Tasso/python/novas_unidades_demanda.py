import json
from shapely.wkt import loads

def get_centroid(geometry):
    geom = loads(geometry)
    centroid = geom.centroid
    return centroid.y, centroid.x

def criar_novos_arquivos(dados):
    niveis = ["Nivel 1", "Nivel 2", "Nivel 3"]
    novos_dados = {nivel: [] for nivel in niveis}
    for item in dados:
        nome_original = item["NOME"]
        geom_str = item["GEOMETRIA"]
        latitude, longitude = get_centroid(geom_str)
        for nivel in niveis:
            novos_dados[nivel].append({
                "name": f"{nivel} {nome_original}",
                "latitude": latitude,
                "longitude": longitude
            })
    for nivel, lista in novos_dados.items():
        file_path = f"P.O Saude/dados_json/novas_unidades_{nivel.lower().replace(' ', '_')}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(lista, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    with open("P.O Saude/dados_json/bairro_demanda_set.json", 'r', encoding='utf-8') as f:
        dados = json.load(f)
    criar_novos_arquivos(dados)
