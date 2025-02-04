import pandas as pd
import json

# Load the Excel file
df = pd.read_excel('df_equipes_terciario.xlsx')

# Filter the DataFrame for employees in BELO HORIZONTE
df_bh = df[df['municipio'] == 'BELO HORIZONTE']

# Group by 'profissional_cbo' and calculate the sum of 'carga_horaria' and 'qntd_eqs'
grouped = df_bh.groupby('profissional_cbo').agg({
    'carga_horaria': 'sum',
    'qntd_eqs': 'sum'
}).reset_index()

# Convert the grouped DataFrame to a list of dictionaries
result = grouped.to_dict(orient='records')

# Save the result to a JSON file
with open('data_excel/funcionarios_bh_terciario.json', 'w') as json_file:
    json.dump(result, json_file, indent=4)