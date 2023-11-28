from typing import List
import z3

def check_constraints(constraints:List[z3.ExprRef])->bool:
    s = z3.Solver()
    for constraint in constraints:
        s.add(constraint)
    return z3.sat == s.check()