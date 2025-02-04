from pulp import LpProblem, LpMinimize, lpSum, LpVariable, GUROBI_CMD,LpBinary
import time
from Data import Data, Data_test

def make_var_name(prefix, *args, max_len=10):
    # Truncate each argument to max_len characters to keep names short
    truncated = [str(arg)[:max_len] for arg in args]
    return prefix + "_" + "_".join(truncated)

class Hierarchical:
    def __init__(self, data: dict):
        self.set_data(data)

    def set_data(self, data):
        self.I = data['I']# pontos de demanda ok
        self.K = data['K']# sem uso
        self.P = data['P']# com ou sem doencças cronicas
        self.E  = data['E']# time  equipe de saude por nivel
        self.EL = data['EL']# unidades de saudes existentes nivel 1 2 3
        self.W = data['W']# tamanho de demanda

        self.CL = data['CL']# unidades candidatas no nivel 1 2 3 
        self.L  = data['L']# total El+Cl
        ########################
        self.CE1 = data['CE1']# custo de equipe 1 
        self.CE2 = data['CE2']# custo de equipe 2
        self.CE3 = data['CE3']# custo de equipe 3
        
        self.D1  = data['D1']# distancia demanda ao nivel 1
        self.D2  = data['D2']# distancia nivel 1 ao 2
        self.D3  = data['D3']# distancia nivel 2 ao 3
        
        self.TC1 = data['TC1']# custo de travessia nivel 1
        self.TC2 = data['TC2']# custo de travessia nivel 2
        self.TC3 = data['TC3']# custo de travessia nivel 3 
        
        self.VC1 = data['VC1']
        self.VC2 = data['VC2']
        self.VC3 = data['VC3']
        
        self.FC1 = data['FC1']
        self.FC2 = data['FC2']
        self.FC3 = data['FC3']
        
        
        self.MS1 = data['MS1']
        self.MS2 = data['MS2']
        self.MS3 = data['MS3']
        
        self.CNES1 = data['CNES1']
        self.CNES2 = data['CNES2']
        self.CNES3 = data['CNES3']
        
        self.C1 = data['C1']
        self.C2 = data['C2']
        self.C3 = data['C3']
        
        self.Uk = data['U']

        self.O1 = data['O1']
        self.O2 = data['O2']

    def Model(self):
        I, K, P, E, EL, CL, L = self.I, self.K, self.P, self.E, self.EL, self.CL, self.L
        VC1, VC2, VC3 = self.VC1, self.VC2, self.VC3
        CE1, CE2, CE3 = self.CE1, self.CE2, self.CE3
        D1, D2, D3 = self.D1, self.D2, self.D3
        TC1, TC2, TC3 = self.TC1, self.TC2, self.TC3
        FC1, FC2, FC3 = self.FC1, self.FC2, self.FC3
        W, MS1, MS2, MS3 = self.W, self.MS1, self.MS2, self.MS3
        CNES1, CNES2, CNES3 = self.CNES1, self.CNES2, self.CNES3
        C1, C2, C3 = self.C1, self.C2, self.C3
        U, O1, O2 = self.Uk, self.O1, self.O2

        # Create numeric mappings for each domain.
        i_map   = {i: str(n) for n, i in enumerate(I, start=1)}
        p_map   = {p: str(n) for n, p in enumerate(P, start=1)}
        l1_map  = {j: str(n) for n, j in enumerate(L[1], start=1)}
        l2_map  = {j: str(n) for n, j in enumerate(L[2], start=1)}
        l3_map  = {j: str(n) for n, j in enumerate(L[3], start=1)}
        e1_map  = {e: str(n) for n, e in enumerate(E[1], start=1)}
        e2_map  = {e: str(n) for n, e in enumerate(E[2], start=1)}
        e3_map  = {e: str(n) for n, e in enumerate(E[3], start=1)}

        model = LpProblem("Hierarchical", LpMinimize)
        
        # Updated variable creation using numeric names.
        y  = {(i, j): LpVariable(name = "y_"+i_map[i] + "_"+l1_map[j], cat=LpBinary) for i in I for j in L[1]}
        y1 = {j: LpVariable(name ="y1_"+l1_map[j], cat=LpBinary) for j in L[1]}
        y2 = {j: LpVariable(name ="y2_"+l2_map[j], cat=LpBinary) for j in L[2]}
        y3 = {j: LpVariable(name ="y3_"+l3_map[j], cat=LpBinary) for j in L[3]}
        
        u1 = {(p, i, j): LpVariable(name ="u1_"+p_map[p] + "_"+i_map[i] + "_"+l1_map[j], lowBound=0) for p in P for i in I for j in L[1]}
        u2 = {(j, j2): LpVariable(name ="u2_"+l1_map[j] + "_"+l2_map[j2], lowBound=0) for j in L[1] for j2 in L[2]}
        u3 = {(j2, j3): LpVariable(name ="u3_"+l2_map[j2] + "_"+l3_map[j3], lowBound=0) for j2 in L[2] for j3 in L[3]}
        
        l1 = {(e, l): LpVariable(name ="l1_"+e1_map[e] + "_"+l1_map[l], lowBound=0) for e in E[1] for l in L[1]}
        l2 = {(e, l): LpVariable(name ="l2_"+e2_map[e] + "_"+l2_map[l], lowBound=0) for e in E[2] for l in L[2]}
        l3 = {(e, l): LpVariable(name ="l3_"+e3_map[e] + "_"+l3_map[l], lowBound=0) for e in E[3] for l in L[3]}
        
        start = time.time()
        print("Objective function")
        model.objective =   lpSum(D1[i][j] * TC1[i][ j] * u1[p,i, j] for p in P for i in I for j in L[1]) + \
                            lpSum(D2[j][ j2] * TC2[j][ j2] * u2[j, j2] for j in L[1] for j2 in L[2]) + \
                            lpSum(D3[j2][ j3] * TC3[j2][ j3] * u3[j2, j3] for j2 in L[2] for j3 in L[3]) + \
                            lpSum(FC1[j]  * y1[j]  for j  in EL[1]) + \
                            lpSum(FC2[j2] * y2[j2] for j2 in EL[2]) + \
                            lpSum(FC3[j3] * y3[j3] for j3 in EL[3]) + \
                            lpSum(CE1[e] * y1[j ] for j  in CL[1] for e in E[1]) + \
                            lpSum(CE2[e] * y2[j2] for j2 in CL[2] for e in E[2]) + \
                            lpSum(CE3[e] * y3[j3] for j3 in CL[3] for e in E[3]) + \
                            lpSum(D1[i ][ j1] * TC1[i ][ j1] * u1[p, i,j1] * VC1[p,j1] for p in P for i  in I    for j1 in L[1]) + \
                            lpSum(D2[j ][ j2] * TC2[j ][ j2] * u2[j,   j2] * VC2[p,j2] for p in P for j  in L[1] for j2 in L[2]) + \
                            lpSum(D3[j2][ j3] * TC3[j2][ j3] * u3[j2,  j3] * VC3[p,j3] for p in P for j2 in L[2] for j3 in L[3])
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("Fix the location variables of existing health care units")
        for j1 in EL[1]: 
            model += y1[j1] == 1
        for j2 in EL[2]: 
            model += y2[j2] == 1
        for j3 in EL[3]: 
            model += y3[j3] == 1
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("Universal coverage")
        for i in I:
            for j in L[1]:
                model += lpSum(u1[p, i, j] for p in P) == lpSum(W[i, p]*y[i,j] for p in P)
        for i in I:
            model += lpSum(y[i,j] for j in L[1]) == 1
        for j in L[1]:
            model += lpSum(u2[j , j2] for j2 in L[2]) == O1[j] * lpSum(u1[p,i, j]for p in P for i in I)
        for j2 in L[2]:
            model += lpSum(u3[j2, j3] for j3 in L[3]) == O2[j2] * lpSum(u2[j, j2] for j in L[1])
            
        # Optimize existing location health care team
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("Optimize existing location health care team")
        for j in EL[1]:
            for e in E[1]:
                model += lpSum(u1[p, i, j] * MS1[e] for p in P for i in I) - l1[e,j ] == CNES1[j][e]
        for j2 in EL[2]:
            for e in E[2]:
                model += lpSum(u2[j, j2] * MS2[e] for j in L[1]) - l2[e,j2] == CNES2[j2][e]
        for j3 in EL[3]:
            for e in E[3]:
                model += lpSum(u3[j2, j3] * MS3[e] for j2 in L[2]) - l3[e,j3] == CNES3[j3][e]
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("Optimize new location health care team")
        for j in CL[1]:
            for e in E[1]:
                model += lpSum(u1[p, i, j] * MS1[e] for p in P for i in I) == l1[e,j ]
        for j2 in CL[2]:
            for e in E[2]:
                model += lpSum(u2[j, j2] * MS2[e] for j in L[1]) == l2[e,j2]
        for j3 in CL[3]:
            for e in E[3]:
                model += lpSum(u3[j2, j3] * MS3[e] for j2 in L[2]) == l3[e,j3]
                
        # Existing health care units have limited capacity
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("Existing health care units have limited capacity")
        for j in EL[1]:
            for p in P:
                            model += lpSum(u1[p,i, j] for i in I)     <= C1[p,j]
        for j2 in EL[2]:    model += lpSum(u2[j, j2] for j in L[1])   <= C2[ j2]
        for j3 in EL[3]:    model += lpSum(u3[j2, j3] for j2 in L[2]) <= C3[ j3]
        
        print("Total time: "  + str(time.time() - start))
        
        start = time.time()
        print("New health care units have limited capacity")
        for j in CL[1]:
            for p in P:
                model += lpSum(u1[p, i, j] for i in I) <= C1[p,j]* y1[j]
        for j2 in CL[2]:
            model += lpSum(u2[j, j2] for j in L[1]) <= C2[j2] * y2[j2]
        for j3 in CL[3]:
            model += lpSum(u3[j2, j3] for j2 in L[2]) <= C3[j3] * y3[j3]
        print("Total time: "  + str(time.time() - start))
        start = time.time()
        print("New health care units have limited capacity")
        model += lpSum(y1[j ] for j  in CL[1]) <= U[1]
        model += lpSum(y2[j2] for j2 in CL[2]) <= U[2]
        model += lpSum(y3[j3] for j3 in CL[3]) <= U[3]
                
        self._model = model
        self.y, self.y1, self.y2, self.y3 = y, y1, y2, y3
        self.u1, self.u2, self.u3 = u1, u2, u3
        self.l1, self.l2, self.l3 = l1, l2, l3

    def run(self):
        print("Solving the model...")
        start_time = time.time()
        self._model.solve()
        end_time = time.time()
        self.solutionTime = end_time - start_time

    def print_solution(self):
        I, K, P, E, EL, CL, L = self.I, self.K, self.P, self.E, self.EL, self.CL, self.L
        VC1, VC2, VC3 = self.VC1, self.VC2, self.VC3
        CE1, CE2, CE3 = self.CE1, self.CE2, self.CE3
        D1, D2, D3 = self.D1, self.D2, self.D3
        TC1, TC2, TC3 = self.TC1, self.TC2, self.TC3
        FC1, FC2, FC3 = self.FC1, self.FC2, self.FC3
        W, MS1, MS2, MS3 = self.W, self.MS1, self.MS2, self.MS3
        CNES1, CNES2, CNES3 = self.CNES1, self.CNES2, self.CNES3
        C1, C2, C3 = self.C1, self.C2, self.C3
        U, O1, O2 = self.Uk, self.O1, self.O2
        
        y, y1, y2, y3 = self.y, self.y1, self.y2, self.y3
        u1, u2, u3 = self.u1, self.u2, self.u3  
        l1, l2, l3 = self.l1, self.l2, self.l3
        
        model = self._model
        if model.status:
            logist_cost =   sum(D1[i][j] * TC1[i][ j] * (u1[p,i, j].value() or 0) for p in P for i in I for j in L[1]) + \
                            sum(D2[j][j2] * TC2[j][ j2] * (u2[j, j2].value() or 0) for j in L[1] for j2 in L[2]) + \
                            sum(D3[j2][ j3] * TC3[j2][ j3] * (u3[j2, j3].value() or 0) for j2 in L[2] for j3 in L[3])
                            
            fixed_cost_E = sum(self.FC1[j] for j in EL[1]) + sum(self.FC2[j] for j in EL[2]) + sum(self.FC3[j] for j in EL[3])
            fixed_cost_C = sum(self.FC1[j1] * (self.y1[j1].value() or 0) for j1 in CL[1]) + sum(self.FC2[j2] * (self.y2[j2].value() or 0) for j2 in CL[2]) + sum(self.FC3[j3] * (self.y3[j3].value() or 0) for j3 in CL[3])
            new_team_cost_C = sum(self.CE1[e] * (self.y1[j1].value() or 0) for j1 in CL[1] for e in E[1]) + sum(self.CE2[e] * (self.y2[j2].value() or 0) for j2 in CL[2] for e in E[2]) + sum(self.CE3[e] * (self.y3[j3].value() or 0) for j3 in CL[3] for e in E[3])
            variable_cost = sum(D1[i][j1] * TC1[i][ j1] * (self.u1[p, i, j1].value() or 0) * VC1[p, j1] for p in P for i in I for j1 in L[1]) + \
                            sum(D2[j1][ j2] * TC2[j1][j2] * (self.u2[j1, j2].value() or 0) * VC2[p, j2] for p in P for j1 in L[1] for j2 in L[2]) + \
                            sum(D3[j2][ j3] * TC3[j2][ j3] * (self.u3[j2, j3].value() or 0) * VC3[p, j3] for p in P for j2 in L[2] for j3 in L[3])
            total = logist_cost + fixed_cost_E + fixed_cost_C + new_team_cost_C + variable_cost
            print("==================================")
            print("Health Care Plan")
            print("==================================")
            print(f"Logist cost: ${logist_cost:.2f}")
            print(f"Fixed cost [E]: ${fixed_cost_E:.2f}")
            print(f"Fixed cost [C]: ${fixed_cost_C:.2f}")
            print(f"New team cost [C]: ${new_team_cost_C:.2f}")
            print(f"Variable Cost: ${variable_cost:.2f}")
            print("==================================")
            print(f"Total Cost: ${total:.2f}")
            print("==================================")
            print("New Units: Qty Max Use(%)")
            print("==================================")
            print(f"PHC : {sum(self.y1[j ].value() for j in CL[1])} {U[1]} {sum(self.y1[j].value() for j in CL[1]) / U[1] * 100:.2f}%")
            print(f"SHC : {sum(self.y2[j2].value() for j2 in CL[2])} {U[2]} {sum(self.y2[j2].value() for j2 in CL[2]) / U[2] * 100:.2f}%")
            print(f"THC : {sum(self.y3[j3].value() for j3 in CL[3])} {U[3]} {sum(self.y3[j3].value() for j3 in CL[3]) / U[3] * 100:.2f}%")
            # print("==================================")
            # print("Municipality: Pop Flow")
            # print("==================================")
            # for i in I:
            #     print(f"[{i} ]: {sum((self.u1[p, i, j].value() or 0) for p in P for j in L[1])} {sum((self.u1[p, i, j].value() or 0) for p in P for j in L[1])}")
            # print("==================================")
            # print("Mun > PHC :(flow)")
            # print("==================================")
            # for i in I:
            #     for j in L[1]:
            #         if (self.u1[1, i, j].value() or 0) > 0:
            #             print(f"M[{i} ] > : {sum((self.u1[p, i, j].value() or 0) for p in P)}")
            #             print(f"> L[{j} ]: {sum((self.u1[p, i, j].value() or 0) for p in P)}")
            # print("==================================")
            # print("PHC > SHC :(flow)")
            # print("==================================")
            # for j in L[1]:
            #     for j2 in L[2]:
            #         if (self.u2[j, j2].value() or 0) > 0:
            #             print(f"L[{j} ] > : {self.u2[j, j2].value() or 0}")
            #             print(f"> L[{j2} ]: {self.u2[j, j2].value() or 0}")
            # print("==================================")
            # print("SHC > THC :(flow)")
            # print("==================================")
            # for j2 in L[2]:
            #     for j3 in L[3]:
            #         if (self.u3[j2, j3].value() or 0) > 0:
            #             print(f"L[{j2} ] > : {self.u3[j2, j3].value() or 0}")
            #             print(f"> L[{j3} ]: {self.u3[j2, j3].value() or 0}")
            # print("==================================")
            # print("==================================")
            # print("Health care team (Existing and New*)")
            # print("==================================")
            # print("==================================")
            # print("PHC-Team CNES Flow Lack/Excess")
            # print("==================================")
            # for j in L[1]:
            #     print(f"L[{j} ]")
            #     for e in E[1]:
            #         flow = sum((self.u1[p, i, j].value() or 0) * MS1[e] for p in P for i in I)
            #         cnes = CNES1[j][e]
            #         print(f"[{e}]: {cnes:.2f} {flow:.2f} {flow - cnes:.2f}")
            # print("==================================")
            # print("SHC-Team CNES Flow Lack/Excess")
            # print("==================================")
            # for j2 in L[2]:
            #     print(f"L[{j2} ]")
            #     for e in E[2]:
            #         flow = sum((self.u2[j, j2].value() or 0) * MS2[e] for j in L[1])
            #         cnes = CNES2[j2][e]
            #         print(f"[{e}]: {cnes:.2f} {flow:.2f} {flow - cnes:.2f}")
            # print("==================================")
            # print("THC-Team CNES Flow Lack/Excess")
            # print("==================================")
            # for j3 in L[3]:
            #     print(f"L[{j3} ]")
            #     for e in E[3]:
            #         flow = sum((self.u3[j2, j3].value() or 0) * MS3[e] for j2 in L[2])
            #         cnes = CNES3[j3][e]
            #         print(f"[{e}]: {cnes:.2f} {flow:.2f} {flow - cnes:.2f}")
            print("==================================")
            print("PHC [p]: Capty Met Use(%)")
            print("==================================")
            for p in P:
                for j in L[1]:
                    capty = C1[p, j]
                    met = sum((self.u1[p, i, j].value() or 0) for i in I)
                    print(f"[{p} ][{j}]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
            print("SHC : Capty Met Use(%)")
            print("==================================")
            for j2 in L[2]:
                capty = C2[j2]
                met = sum((self.u2[j, j2].value() or 0) for j in L[1])
                print(f"[{j2} ]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
            print("THC : Capty Met Use(%)")
            print("==================================")
            for j3 in L[3]:
                capty = C3[j3]
                met = sum((self.u3[j2, j3].value() or 0) for j2 in L[2])
                print(f"[{j3} ]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
        else:
            print("No optimal solution found.")

    def validate_model(self):
        print("=== Validating Model ===")
        errors = []
        try:
            assert len(self.I) > 0, "O conjunto I está vazio."
            assert len(self.K) > 0, "O conjunto K está vazio."
            assert len(self.P) > 0, "O conjunto P está vazio."
            assert len(self.L) > 0, "O conjunto L está vazio."
            assert len(self.D1) > 0, "A matriz de distâncias D1 está vazia."
            assert len(self.D2) > 0, "A matriz de distâncias D2 está vazia."
            assert len(self.D3) > 0, "A matriz de distâncias D3 está vazia."
        except AssertionError as e:
            errors.append(f"Erro nos dados de entrada: {e}")
    
        # Verificar valores repetidos e itens em comum
        if len(self.I) != len(set(self.I)):
            errors.append("Existem valores repetidos no conjunto I.")
        if len(self.K) != len(set(self.K)):
            errors.append("Existem valores repetidos no conjunto K.")
        if len(self.P) != len(set(self.P)):
            errors.append("Existem valores repetidos no conjunto L.")

        common_items = set(self.I) & set(self.K) & set(self.P) & set(self.L)
        if common_items:
            errors.append(f"Existem itens em comum entre os conjuntos I, K, P e L: {common_items}")

        def check_variable_duplicates(variables, name):
            variable_names = [var.name for var in variables.values()]
            duplicates = [name for name in set(variable_names) if variable_names.count(name) > 1]
            if duplicates: errors.append(f"Duplicatas encontradas nas variáveis {name}: {duplicates}")

        check_variable_duplicates(self.y1, "y1")
        check_variable_duplicates(self.y2, "y2")
        check_variable_duplicates(self.y3, "y3")

        # Verificar inconsistências gerais
        for j in self.L[1]:
            for p in self.P:
                if self.C1[p,j] <= 0:
                    errors.append(f"Custo de nível 1 inválido para a instalação {j}.")
        for j2 in self.L[2]:
            if self.C2[j2] <= 0:
                errors.append(f"Custo de nível 2 inválido para a instalação {j2}.")
        for j3 in self.L[3]:
            if self.C3[j3] <= 0:
                errors.append(f"Custo de nível 3 inválido para a instalação {j3}.")

        # Mostrar resultados
        if errors:
            print("### Erros encontrados no modelo: ###")
            for error in errors:
                print(f"- {error}")
            return False
        else:
            print("Validação concluída: Nenhum erro encontrado.")
            return True

    def export_model(self, filename="model.lp"):
        self._model.writeLP(filename)

if __name__ == "__main__":
    # data = Data_test()
    data = Data()

    hierarchical_model = Hierarchical(data.get_data())
    hierarchical_model.Model()

    # Export the model to an LP file for debugging
    hierarchical_model.export_model("debug_model.lp")

    # Validar modelo antes de resolver
    # if hierarchical_model.validate_model():
    hierarchical_model.run()
    hierarchical_model.print_solution()
    # else:
    #     print("O modelo contém erros e não pode ser resolvido.")
