from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.transaction.symbolic import ACTORS
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
    if 'DELEGATECALL' in annotation.state_trace:
        trace_states = annotation.state_trace['DELEGATECALL']
        for trace_state in trace_states:
            to = trace_state.mstate.stack[-2]
            
            try:
                model = get_model(tuple(trace_state.world_state.constraints+[to==ACTORS.attacker]), enforce_execution_time = False)
                raise Complete
            except UnsatError:
                pass

def arbitrary_delegate_call(disassembly:Disassembly, transaction_count:int = 1)->bool:
    has_delegate_call = False
    for instr in disassembly.instruction_list:
        if instr['opcode'] == 'DELEGATECALL':
            has_delegate_call = True
            break
    if not has_delegate_call:
        return False
    
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec(disassembly, transaction_count=transaction_count, concrete_storage=True, opcodes_trace=['DELEGATECALL'])
    except Complete:
        return True
    if len(final_states) == 0:
        raise NoFinalState
    return False