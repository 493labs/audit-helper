from mythril.support.model import get_model
from mythril.exceptions import UnsatError
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from bytecode.frame.annotation.state_trace import StateTraceAnnotation
from bytecode.frame.annotation.base import get_first_annotation
from bytecode.analyze.excepts.base import NoFinalState
from bytecode.support.analyze_result import analyze_use_db, DB_FLAG
from bytecode.frame.svm import SVM

class Complete(Exception):
    pass

def final_state_hook(final_state:GlobalState):
    annotation:StateTraceAnnotation = get_first_annotation(final_state, StateTraceAnnotation)
    if not annotation:
        return
    if 'SSTORE' in annotation.state_trace:
        trace_states = annotation.state_trace['SSTORE']
        for trace_state in trace_states:
            slot = trace_state.mstate.stack[-1]
            
            try:
                model = get_model(tuple(trace_state.world_state.constraints+[slot==1000]), enforce_execution_time = False)
                raise Complete
            except UnsatError:
                pass

@analyze_use_db(key='arbitrary_write_check')
def arbitrary_write_check(disassembly:Disassembly, db_flag:DB_FLAG = DB_FLAG.NoUse, db = None)->bool:
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec_liner(disassembly, concrete_storage=True, opcodes_trace=['SSTORE'])
    except Complete:
        return True
    if len(final_states) == 0:
        return False
        # raise NoFinalState
    return False
