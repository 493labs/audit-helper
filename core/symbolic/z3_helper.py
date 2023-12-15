from typing import List
import z3

def check_constraints(constraints:List[z3.ExprRef])->bool:
    s = z3.Optimize()
    for constraint in constraints:
        s.add(constraint)
    return z3.sat == s.check()

def solve_constraints(constraints:List[z3.ExprRef])->z3.ModelRef:
    s = z3.Optimize()
    for constraint in constraints:
        s.add(constraint)
    result = s.check()
    if result == z3.sat:
        model = s.model()
        return model
    else:
        return None
    
def gene_z3_var_from_elementary(z3_name:str, elementary_name:str):
    if elementary_name.startswith('uint'):
        return z3.Int(z3_name)
    
    elif elementary_name.startswith('int'):
        return z3.Int(z3_name)
    
    elif elementary_name == 'address':
        assert False, "地址变量应该赋具体值"
        
    else:
        assert False, '未处理的类型'

def simplify(expr: z3.ExprRef):
    if type(expr) == bool:
        return expr
    return z3.simplify(expr)
