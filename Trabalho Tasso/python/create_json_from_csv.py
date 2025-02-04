import geopandas as gpd
import pandas as pd
import json
from shapely import wkt

def convert_utm_to_latlon(geometry, utm_zone=23, southern_hemisphere=True):
    # Define the UTM projection and the WGS84 projection
    utm_proj = f"+proj=utm +zone={utm_zone} +south={southern_hemisphere} +ellps=WGS84"
    wgs84_proj = "+proj=longlat +datum=WGS84 +no_defs"
    
    # Convert the geometry to WGS84
    geometry = geometry.to_crs(wgs84_proj)
    return geometry

def create_json_from_custom_csv(csv_file, json_file):
    # Load the CSV file with custom delimiter
    df = pd.read_csv(csv_file, delimiter=';')

    # Convert the 'GEOMETRIA' column from WKT to geometries
    df['GEOMETRIA'] = df['GEOMETRIA'].apply(wkt.loads)
    
    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='GEOMETRIA')
    
    # Set the CRS for the GeoDataFrame
    gdf.set_crs(epsg=32723, inplace=True)  # Assuming UTM zone 23S
    
    # Convert the geometries from UTM to WGS84
    gdf['GEOMETRIA'] = convert_utm_to_latlon(gdf['GEOMETRIA'])
    
    # Select the required columns
    gdf_selected = gdf[['NOME', 'QTDPESSOAS', 'ID_BAIRRO', 'GEOMETRIA']]
    
    # Convert the GeoDataFrame to a list of dictionaries
    result = gdf_selected.to_dict(orient='records')
    
    # Save the result to a JSON file
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4, default=str)

# Example usage
create_json_from_custom_csv('P.O Saude/data_excel/populacao_domicilio_bairro_2022.csv', 'P.O Saude/dados_json/bairro_demanda_set.json')