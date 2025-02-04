import json

class Data:
    def __init__(self):
        self.demand_file = 'P.O Saude/dados_json/bairro_demanda_set.json'
        self.level_files = {
            1: 'P.O Saude/dados_json/EL_1.json',
            2: 'P.O Saude/dados_json/EL_2.json',
            3: 'P.O Saude/dados_json/EL_3.json'}
        self.equipe_files = {
            1: 'P.O Saude/dados_json/Equipe_1.json',
            2: 'P.O Saude/dados_json/Equipe_2.json',
            3: 'P.O Saude/dados_json/Equipe_3.json'}
        self.cnes_files = {
            1: 'P.O Saude/dados_json/CNES_1.json',
            2: 'P.O Saude/dados_json/CNES_2.json',
            3: 'P.O Saude/dados_json/CNES_3.json'}
        self.distance_files = {
            1: 'P.O Saude/dados_json/distance_matrix_1.json',
            2: 'P.O Saude/dados_json/distance_matrix_2.json',
            3: 'P.O Saude/dados_json/distance_matrix_3.json'}
        self.newLevel_files = {
            1: 'P.O Saude/dados_json/novas_unidades_nivel_1.json',
            2: 'P.O Saude/dados_json/novas_unidades_nivel_2.json',
            3: 'P.O Saude/dados_json/novas_unidades_nivel_3.json'}

    def load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def get_data(self):
        demand_data = self.load_json(self.demand_file)
        level_data = {level: self.load_json(file) for level, file in self.level_files.items()}
        equipe_data = {level: self.load_json(file) for level, file in self.equipe_files.items()}
        cnes_data = {level: self.load_json(file) for level, file in self.cnes_files.items()}
        distance_data = {level: self.load_json(file) for level, file in self.distance_files.items()}
        newLevel_data = {level: self.load_json(file) for level, file in self.newLevel_files.items()}
        I = [d['NOME'] for d in demand_data]
        K = [1, 2, 3]
        P = [1, 2]

        E = {level: list(equipe["descricao_cbo"]) for level, equipe in equipe_data.items()}                   
        EL = {level: [el['name'] for el in data] for level, data in level_data.items()}
        CL = {level: [el['name'] for el in data] for level, data in newLevel_data.items()}
        L = {level: EL.get(level, []) + CL.get(level, []) for level in set(EL.keys()).union(CL.keys())}

        CE = {level: {e: 1000 for e in equipe['descricao_cbo']} for level, equipe in equipe_data.items()}
        
        D1 = distance_data[1]
        D2 = distance_data[2]
        D3 = distance_data[3]

        # Fixed generation of TC1, TC2, TC3 using dictionary comprehensions
        TC1 = {i: {j: 0.5 for j in D1[i].keys()} for i in D1}
        TC2 = {i: {j: 0.5 for j in D2[i].keys()} for i in D2}
        TC3 = {i: {j: 0.5 for j in D3[i].keys()} for i in D3}

        VC1 = {(p, el): 5 for p in P for el in L[1]}
        VC2 = {(p, el): 10 for p in P for el in L[2]}
        VC3 = {(p, el): 20 for p in P for el in L[3]}

        FC1 = {el: 1000 for el in L[1]}
        FC2 = {el: 200 for el in L[2]}
        FC3 = {el: 300 for el in L[3]}

        W = {(d['NOME'], 1): d['QTDPESSOAS'] * 0.6 for d in demand_data}
        W.update({(d['NOME'], 2): d['QTDPESSOAS'] * 0.4 for d in demand_data})

        MS1 = {e: 0.02 for e in E[1]}
        MS2 = {e: 0.01 for e in E[2]}
        MS3 = {e: 0.01 for e in E[3]}

        CNES1 = cnes_data[1]
        CNES2 = cnes_data[2]
        CNES3 = cnes_data[3]

        C1 = {(p, el): 10000 for p in P for el in L[1]}
        C2 = {el: 100000 for el in L[2]}
        C3 = {el: 100000 for el in L[3]}

        U = {1: 10, 2: 10, 3: 10}
        O1 = {el: 0.4 for el in L[1]}
        O2 = {el: 0.7 for el in L[2]}

        return {
            'I': I,
            'K': K,
            'P': P,
            'E': E,
            'EL': EL,
            'CL': CL,
            'L': L,
            'CE1': CE[1],
            'CE2': CE[2],
            'CE3': CE[3],
            'D1': D1,
            'D2': D2,
            'D3': D3,
            'TC1': TC1,
            'TC2': TC2,
            'TC3': TC3,
            'VC1': VC1,
            'VC2': VC2,
            'VC3': VC3,
            'FC1': FC1,
            'FC2': FC2,
            'FC3': FC3,
            'W': W,
            'MS1': MS1,
            'MS2': MS2,
            'MS3': MS3,
            'CNES1': CNES1,
            'CNES2': CNES2,
            'CNES3': CNES3,
            'C1': C1,
            'C2': C2,
            'C3': C3,
            'U': U,
            'O1': O1,
            'O2': O2
        }

class Data_test:
    def get_data(self):
        return {
            'I': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            'K': [1, 2, 3],
            'P': [1, 2],
            'E': {
            1: ['ME1', 'EF1', 'ACS', 'DE1'],
            2: ['ME2', 'EF2', 'FON', 'OCD', 'DE2'],
            3: ['ME3', 'EF3', 'TE3', 'FIS', 'DE3']
            },
            'EL': {
            1: [1, 2, 3, 4, 5, 6],
            2: [1, 2, 3, 4],
            3: [1, 2, 3]
            },
            'CL': {
            1: [7, 8, 9, 10],
            2: [5, 6, 7, 8],
            3: [4, 5, 6]
            },
            'L': {
            1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            2: [1, 2, 3, 4, 5, 6, 7, 8],
            3: [1, 2, 3, 4, 5, 6]
            },
            'CE1': {'ME1': 10, 'EF1': 10, 'ACS': 10, 'DE1': 10},
            'CE2': {'ME2': 20, 'EF2': 20, 'FON': 20, 'OCD': 20, 'DE2': 20},
            'CE3': {'ME3': 30, 'EF3': 30, 'TE3': 30, 'FIS': 30, 'DE3': 30},
            'D1': {i: {j: 1 for j in range(1, 11)}for i in range(1, 16) },
            'D2': {i: {j: 1  for j in range(1, 9)} for i in range(1, 11)},
            'D3': {i: {j: 1  for j in range(1, 7)}for i in range(1, 9)},
            'TC1': {i: {j: 1 for j in range(1, 11)} for i in range(1, 16) },
            'TC2': {i: {j: 1 for j in range(1, 9)} for i in range(1, 11) },
            'TC3': {i: {j: 1  for j in range(1, 7)} for i in range(1, 9)},
            'VC1': {(i,j): 5 for i in range(1, 3) for j in range(1, 11)},
            'VC2': {(i,j): 10 for i in range(1, 3) for j in range(1, 9)},
            'VC3': {(i,j): 20 for i in range(1, 3) for j in range(1, 7)},
            'FC1': {i: 1000 if i <= 6 else 100 for i in range(1, 11)},
            'FC2': {i: 200 for i in range(1, 9)},
            'FC3': {i: 300 for i in range(1, 7)},
            'W': {(i, j): 100 if j == 1 else 200 for i in range(1, 16) for j in range(1, 3)},
            'MS1': {'ME1': 0.02, 'EF1': 0.002, 'ACS': 0.002, 'DE1': 0.002},
            'MS2': {'ME2': 0.01, 'EF2': 0.01, 'FON': 0.01, 'OCD': 0.01, 'DE2': 0.01},
            'MS3': {'ME3': 0.01, 'EF3': 0.02, 'TE3': 0.01, 'FIS': 0.02, 'DE3': 0.01},
            'CNES1': {j: {e: 5 for e in ['ME1', 'EF1', 'ACS', 'DE1']} for j in range(1, 11)},
            'CNES2': {j: {e: 3 for e in ['ME2', 'EF2', 'FON', 'OCD', 'DE2']} for j in range(1, 9)},
            'CNES3': {j: {e: 2 for e in ['ME3', 'EF3', 'TE3', 'FIS', 'DE3']} for j in range(1, 7)},
            'C1': {
            (1, 1): 1000, (1, 2): 1000, (1, 3): 1000, (1, 4): 1000, (1, 5): 1000, (1, 6): 1000,
            (1, 7): 1000, (1, 8): 500, (1, 9): 500, (1, 10): 500,
            (2, 1): 1000, (2, 2): 1000, (2, 3): 1000, (2, 4): 1000, (2, 5): 1000, (2, 6): 1000,
            (2, 7): 1000, (2, 8): 500, (2, 9): 500, (2, 10): 500
            },
            'C2': {1: 1000,2: 100,3: 100,4: 200,5: 200,6: 200,7: 200,8: 200},
            'C3': {i: 300 for i in range(1, 7)},
            'U': {1: 4, 2: 3, 3: 2},
            'O1': {i: 0.4 for i in range(1, 11)},
            'O2': {i: 0.7 for i in range(1, 9)}
        }
if __name__ == "__main__":
    Data().get_data()