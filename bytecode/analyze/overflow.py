from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from mythril.laser.smt import ULT
from bytecode.util.evm import slot_to_bitvec
from bytecode.frame.svm import SVM
from bytecode.frame.annotation.base import get_first_annotation
from bytecode.frame.annotation.state_trace import StateTraceAnnotation
from bytecode.analyze.excepts.base import NoFinalState
from mythril.support.model import get_model
from mythril.exceptions import UnsatError

class Complete(Exception):
    pass

def final_state_hook(final_state:GlobalState):
    annotation:StateTraceAnnotation = get_first_annotation(final_state, StateTraceAnnotation)
    trace_states = annotation.state_trace['SUB']
    for trace_state in trace_states:
        a = slot_to_bitvec(trace_state.mstate.stack[-1])
        b = slot_to_bitvec(trace_state.mstate.stack[-2])
        
        try:
            model = get_model(tuple(trace_state.world_state.constraints+[ULT(a,b)]), enforce_execution_time = False)
            raise Complete
        except UnsatError:
            pass
    
def overflow_check(disassembly:Disassembly)->bool:
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec(disassembly, opcodes_trace=['SUB'])
    except Complete:
        return True
    if len(final_states) == 0:
        raise NoFinalState
    return False