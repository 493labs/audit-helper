from scheme import Scheme
from slither.core.declarations import Contract, Function
from typing import Mapping, Tuple, List
from core.general.nodes.ex_call.reentrant import iter_analyze_function

def has_nonReentrant_mechanism(f:Function) -> bool:
    '''
    是否具有防重入机制
    '''
    for m in f.modifiers:
        if m.name == 'nonReentrant':
            return True
    return False

def check_readonly_reentrant(scheme:Scheme):
    if scheme.readonly_reentrant_analyzed:
        return
    for f in scheme.c.functions_entry_points:
        if f.is_constructor:
            continue
        has_external_call,i,_,state_variables_written_post  = iter_analyze_function(f)
        if has_external_call and state_variables_written_post:
            for ff in f.contract.functions_entry_points:
                if ff == f or ff.is_constructor or ff.pure or has_nonReentrant_mechanism(ff):
                    continue
                if set(state_variables_written_post) & set(ff.all_state_variables_read()):
                    if ff.view:
                        scheme.readonly_reentrant_risk_funcs.append(ff)
    scheme.readonly_reentrant_analyzed = True