from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from bytecode.frame.svm import SVM
from bytecode.frame.annotation.base import get_first_annotation
from bytecode.frame.annotation.state_trace import StateTraceAnnotation
from bytecode.analyze.excepts.base import NoFinalState
from bytecode.support.analyze_result import analyze_use_db, DB_FLAG
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

@analyze_use_db('arbitrary_delegate_call')
def arbitrary_delegate_call(disassembly:Disassembly, transaction_count:int = 1, db_flag:DB_FLAG = DB_FLAG.NoUse, db = None)->bool:
    if not has_delegate_call(disassembly):
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

@analyze_use_db('arbitrary_delegate_call')
def arbitrary_delegate_call2(disassembly:Disassembly, db_flag:DB_FLAG = DB_FLAG.NoUse, db = None)->bool:
    if not has_delegate_call(disassembly):
        return False
    
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec(disassembly, concrete_storage=True, opcodes_trace=['DELEGATECALL','SSTORE'])
    except Complete:
        return True
    if len(final_states) == 0:
        raise NoFinalState
    
    from bytecode.frame.annotation.state_trace import get_state_trace
    from bytecode.frame.annotation.smt.bitvec_info import get_slot_source
    delegate_call_slot_reads = []
    for final_state in final_states:
        delegatecall_states = get_state_trace(final_state, 'DELEGATECALL')
        for delegatecall_state in delegatecall_states:
            slot_source = get_slot_source(delegatecall_state.mstate.stack[-2])
            if slot_source:
                delegate_call_slot_reads.append(slot_source)
    for final_state in final_states:
        sstore_states = get_state_trace(final_state, 'SSTORE')
        for sstore_state in sstore_states:
            for slot_read in delegate_call_slot_reads:
                try:
                    model = get_model(
                        tuple(sstore_state.world_state.constraints + [
                            sstore_state.mstate.stack[-1] == slot_read,
                            sstore_state.mstate.stack[-2] == ACTORS.attacker
                        ]), enforce_execution_time = False
                    )
                    return True
                except UnsatError:
                    pass
    return False

@analyze_use_db('arbitrary_delegate_call')
def arbitrary_delegate_call3(disassembly:Disassembly, db_flag:DB_FLAG = DB_FLAG.NoUse, db = None)->bool:
    if not has_delegate_call(disassembly):
        return False
    
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec_liner(disassembly, concrete_storage=True, opcodes_trace=['DELEGATECALL'])
    except Complete:
        return True
    if len(final_states) == 0:
        raise NoFinalState
    return False

def has_delegate_call(disassembly:Disassembly) -> bool:
    for instr in disassembly.instruction_list:
        if instr['opcode'] == 'DELEGATECALL':
            return True
    return False