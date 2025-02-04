import gurobipy as gp
from gurobipy import GRB
import time
from Data import Data, Data_test

class Hierarchical:
    def __init__(self, data: dict):
        self.set_data(data)

    def set_data(self, data):
        self.I = data['I']
        self.K = data['K']
        self.P = data['P']
        self.E  = data['E']
        self.EL = data['EL']
        self.W = data['W']
        self.CL = data['CL']
        self.L  = data['L']
        self.CE1 = data['CE1']
        self.CE2 = data['CE2']
        self.CE3 = data['CE3']
        self.D1  = data['D1']
        self.D2 = data['D2']
        self.D3 = data['D3']
        self.TC1 = data['TC1']
        self.TC2 = data['TC2']
        self.TC3 = data['TC3']
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
        model = gp.Model("Hierarchical")
        
        # Batch variable creation using addVars
        y  = model.addVars(self.I, self.L[1], vtype=GRB.BINARY, name="y")
        y1 = model.addVars(self.L[1], vtype=GRB.BINARY, name="y1")
        y2 = model.addVars(self.L[2], vtype=GRB.BINARY, name="y2")
        y3 = model.addVars(self.L[3], vtype=GRB.BINARY, name="y3")
        
        u1 = model.addVars(self.P, self.I, self.L[1], lb=0, vtype=GRB.CONTINUOUS, name="u1")
        u2 = model.addVars(self.L[1], self.L[2], lb=0, vtype=GRB.CONTINUOUS, name="u2")
        u3 = model.addVars(self.L[2], self.L[3], lb=0, vtype=GRB.CONTINUOUS, name="u3")
        
        l1 = model.addVars(self.E[1], self.L[1], vtype=GRB.CONTINUOUS, name="l1")
        l2 = model.addVars(self.E[2], self.L[2], vtype=GRB.CONTINUOUS, name="l2")
        l3 = model.addVars(self.E[3], self.L[3], vtype=GRB.CONTINUOUS, name="l3")
        
        # Objective function remains unchanged
        obj = gp.quicksum(self.D1[i][j] * self.TC1[i][j] * u1[p,i,j] for p in self.P for i in self.I for j in self.L[1]) + \
              gp.quicksum(self.D2[j][j2] * self.TC2[j][j2] * u2[j,j2] for j in self.L[1] for j2 in self.L[2]) + \
              gp.quicksum(self.D3[j2][j3] * self.TC3[j2][j3] * u3[j2,j3] for j2 in self.L[2] for j3 in self.L[3]) + \
              gp.quicksum(self.FC1[j] * y1[j] for j in self.EL[1]) + \
              gp.quicksum(self.FC2[j2] * y2[j2] for j2 in self.EL[2]) + \
              gp.quicksum(self.FC3[j3] * y3[j3] for j3 in self.EL[3]) + \
              gp.quicksum(self.CE1[e] * y1[j] for j in self.CL[1] for e in self.E[1]) + \
              gp.quicksum(self.CE2[e] * y2[j2] for j2 in self.CL[2] for e in self.E[2]) + \
              gp.quicksum(self.CE3[e] * y3[j3] for j3 in self.CL[3] for e in self.E[3]) + \
              gp.quicksum(self.D1[i][j1] * self.TC1[i][j1] * u1[p,i,j1] * self.VC1[p,j1] for p in self.P for i in self.I for j1 in self.L[1]) + \
              gp.quicksum(self.D2[j][j2] * self.TC2[j][j2] * u2[j,j2] * self.VC2[p,j2] for p in self.P for j in self.L[1] for j2 in self.L[2]) + \
              gp.quicksum(self.D3[j2][j3] * self.TC3[j2][j3] * u3[j2,j3] * self.VC3[p,j3] for p in self.P for j2 in self.L[2] for j3 in self.L[3])
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Fix the location variables of existing health care units
        model.addConstrs((y1[j1] == 1 for j1 in self.EL[1]), name="fix_y1")
        model.addConstrs((y2[j2] == 1 for j2 in self.EL[2]), name="fix_y2")
        model.addConstrs((y3[j3] == 1 for j3 in self.EL[3]), name="fix_y3")
        
        start = time.time()
        print("Universal coverage")
        for i in self.I:
            for j in self.L[1]:
                model.addConstr(gp.quicksum(u1[p,i,j] for p in self.P) == gp.quicksum(self.W[i,p] * y[i,j] for p in self.P))
        for i in self.I:
            model.addConstr(gp.quicksum(y[i,j] for j in self.L[1]) == 1)
        for j in self.L[1]:
            model.addConstr(gp.quicksum(u2[j,j2] for j2 in self.L[2]) == self.O1[j] * gp.quicksum(u1[p,i,j] for p in self.P for i in self.I))
        for j2 in self.L[2]:
            model.addConstr(gp.quicksum(u3[j2,j3] for j3 in self.L[3]) == self.O2[j2] * gp.quicksum(u2[j,j2] for j in self.L[1]))
        print("Total time: " + str(time.time() - start))
        
        start = time.time()
        print("Optimize existing location health care team")
        for j in self.EL[1]:
            for e in self.E[1]:
                model.addConstr(gp.quicksum(u1[p,i,j] * self.MS1[e] for p in self.P for i in self.I) - l1[e,j] == self.CNES1[j][e])
        for j2 in self.EL[2]:
            for e in self.E[2]:
                model.addConstr(gp.quicksum(u2[j,j2] * self.MS2[e] for j in self.L[1]) - l2[e,j2] == self.CNES2[j2][e])
        for j3 in self.EL[3]:
            for e in self.E[3]:
                model.addConstr(gp.quicksum(u3[j2,j3] * self.MS3[e] for j2 in self.L[2]) - l3[e,j3] == self.CNES3[j3][e])
        print("Total time: " + str(time.time() - start))
        
        start = time.time()
        print("Optimize new location health care team")
        for j in self.CL[1]:
            for e in self.E[1]:
                model.addConstr(gp.quicksum(u1[p,i,j] * self.MS1[e] for p in self.P for i in self.I) == l1[e,j])
        for j2 in self.CL[2]:
            for e in self.E[2]:
                model.addConstr(gp.quicksum(u2[j,j2] * self.MS2[e] for j in self.L[1]) == l2[e,j2])
        for j3 in self.CL[3]:
            for e in self.E[3]:
                model.addConstr(gp.quicksum(u3[j2,j3] * self.MS3[e] for j2 in self.L[2]) == l3[e,j3])
        print("Total time: " + str(time.time() - start))
        
        start = time.time()
        print("Existing health care units have limited capacity")
        for j in self.EL[1]:
            for p in self.P:
                model.addConstr(gp.quicksum(u1[p,i,j] for i in self.I) <= self.C1[p,j])
        for j2 in self.EL[2]:
            model.addConstr(gp.quicksum(u2[j,j2] for j in self.L[1]) <= self.C2[j2])
        for j3 in self.EL[3]:
            model.addConstr(gp.quicksum(u3[j2,j3] for j2 in self.L[2]) <= self.C3[j3])
        print("Total time: " + str(time.time() - start))
        
        start = time.time()
        print("New health care units have limited capacity")
        for j in self.CL[1]:
            for p in self.P:
                model.addConstr(gp.quicksum(u1[p,i,j] for i in self.I) <= self.C1[p,j] * y1[j])
        for j2 in self.CL[2]:
            model.addConstr(gp.quicksum(u2[j,j2] for j in self.L[1]) <= self.C2[j2] * y2[j2])
        for j3 in self.CL[3]:
            model.addConstr(gp.quicksum(u3[j2,j3] for j2 in self.L[2]) <= self.C3[j3] * y3[j3])
        print("Total time: " + str(time.time() - start))
        
        start = time.time()
        print("New health care units selection limit")
        model.addConstr(gp.quicksum(y1[j] for j in self.CL[1]) <= self.Uk[1])
        model.addConstr(gp.quicksum(y2[j2] for j2 in self.CL[2]) <= self.Uk[2])
        model.addConstr(gp.quicksum(y3[j3] for j3 in self.CL[3]) <= self.Uk[3])
        print("Total time: " + str(time.time() - start))
        
        # Store the model and variables for later use
        self._model = model
        self.y = y
        self.y1 = y1
        self.y2 = y2
        self.y3 = y3
        self.u1 = u1
        self.u2 = u2
        self.u3 = u3
        self.l1 = l1
        self.l2 = l2
        self.l3 = l3

        return model

    def run(self):
        print("Solving the model...")
        start_time = time.time()
        self._model.optimize()  # use optimize() for gurobipy
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
        if model.status == GRB.OPTIMAL:
            logist_cost = sum(D1[i][j] * TC1[i][j] * (u1[p,i,j].X if u1[p,i,j].X is not None else 0) for p in P for i in I for j in L[1]) + \
                          sum(D2[j][j2] * TC2[j][j2] * (u2[j,j2].X if u2[j,j2].X is not None else 0) for j in L[1] for j2 in L[2]) + \
                          sum(D3[j2][j3] * TC3[j2][j3] * (u3[j2,j3].X if u3[j2,j3].X is not None else 0) for j2 in L[2] for j3 in L[3])
            
            fixed_cost_E = sum(FC1[j] for j in EL[1]) + sum(FC2[j2] for j2 in EL[2]) + sum(FC3[j3] for j3 in EL[3])
            fixed_cost_C = sum(FC1[j1] * (y1[j1].X if y1[j1].X is not None else 0) for j1 in CL[1]) + \
                           sum(FC2[j2] * (y2[j2].X if y2[j2].X is not None else 0) for j2 in CL[2]) + \
                           sum(FC3[j3] * (y3[j3].X if y3[j3].X is not None else 0) for j3 in CL[3])
            new_team_cost_C = sum(CE1[e] * (y1[j1].X if y1[j1].X is not None else 0) for j1 in CL[1] for e in E[1]) + \
                              sum(CE2[e] * (y2[j2].X if y2[j2].X is not None else 0) for j2 in CL[2] for e in E[2]) + \
                              sum(CE3[e] * (y3[j3].X if y3[j3].X is not None else 0) for j3 in CL[3] for e in E[3])
            variable_cost = sum(D1[i][j1] * TC1[i][j1] * (u1[p,i,j1].X if u1[p,i,j1].X is not None else 0) * VC1[p,j1] for p in P for i in I for j1 in L[1]) + \
                            sum(D2[j1][j2] * TC2[j1][j2] * (u2[j1,j2].X if u2[j1,j2].X is not None else 0) * VC2[p,j2] for p in P for j1 in L[1] for j2 in L[2]) + \
                            sum(D3[j2][j3] * TC3[j2][j3] * (u3[j2,j3].X if u3[j2,j3].X is not None else 0) * VC3[p,j3] for p in P for j2 in L[2] for j3 in L[3])
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
            print(f"PHC : {sum(y1[j1].X for j1 in CL[1])} {U[1]} {sum(y1[j1].X for j1 in CL[1]) / U[1] * 100:.2f}%")
            print(f"SHC : {sum(y2[j2].X for j2 in CL[2])} {U[2]} {sum(y2[j2].X for j2 in CL[2]) / U[2] * 100:.2f}%")
            print(f"THC : {sum(y3[j3].X for j3 in CL[3])} {U[3]} {sum(y3[j3].X for j3 in CL[3]) / U[3] * 100:.2f}%")
            print("==================================")
            print("Municipality: Pop Flow")
            print("==================================")
            for i in I:
                flow = sum((u1[p,i,j].X if u1[p,i,j].X is not None else 0) for p in P for j in L[1])
                print(f"[{i} ]: {flow} {flow}")
            print("==================================")
            print("Mun > PHC :(flow)")
            print("==================================")
            for i in I:
                for j in L[1]:
                    if (u1[1,i,j].X if u1[1,i,j].X is not None else 0) > 0:
                        print(f"M[{i} ] > : {sum((u1[p,i,j].X if u1[p,i,j].X is not None else 0) for p in P)}")
                        print(f"> L[{j} ]: {sum((u1[p,i,j].X if u1[p,i,j].X is not None else 0) for p in P)}")
            print("==================================")
            print("PHC > SHC :(flow)")
            print("==================================")
            for j in L[1]:
                for j2 in L[2]:
                    if (u2[j,j2].X if u2[j,j2].X is not None else 0) > 0:
                        print(f"L[{j} ] > : {u2[j,j2].X if u2[j,j2].X is not None else 0}")
                        print(f"> L[{j2} ]: {u2[j,j2].X if u2[j,j2].X is not None else 0}")
            print("==================================")
            print("SHC > THC :(flow)")
            print("==================================")
            for j2 in L[2]:
                for j3 in L[3]:
                    if (u3[j2,j3].X if u3[j2,j3].X is not None else 0) > 0:
                        print(f"L[{j2} ] > : {u3[j2,j3].X if u3[j2,j3].X is not None else 0}")
                        print(f"> L[{j3} ]: {u3[j2,j3].X if u3[j2,j3].X is not None else 0}")
            print("==================================")
            print("PHC [p]: Capty Met Use(%)")
            print("==================================")
            for p in P:
                for j in L[1]:
                    capty = C1[p,j]
                    met = sum((u1[p,i,j].X if u1[p,i,j].X is not None else 0) for i in I)
                    print(f"[{p} ][{j}]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
            print("SHC : Capty Met Use(%)")
            print("==================================")
            for j2 in L[2]:
                capty = C2[j2]
                met = sum((u2[j,j2].X if u2[j,j2].X is not None else 0) for j in L[1])
                print(f"[{j2} ]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
            print("THC : Capty Met Use(%)")
            print("==================================")
            for j3 in L[3]:
                capty = C3[j3]
                met = sum((u3[j2,j3].X if u3[j2,j3].X is not None else 0) for j2 in L[2])
                print(f"[{j3} ]: {capty} {met} {met / capty * 100:.2f}%")
            print("==================================")
        else:
            print("No optimal solution found.")
            
if __name__ == "__main__":
    # data = Data_test()
    data = Data()

    hierarchical_model = Hierarchical(data.get_data())
    hierarchical_model.Model()

    hierarchical_model.print_solution()