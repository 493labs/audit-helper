from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from typing import List, Mapping
from copy import copy, deepcopy

class StateTraceAnnotation(StateAnnotation):
    def __init__(self, watch_list = None, state_trace = None):
        self.watch_list:List[str] = watch_list or []
        self.state_trace:Mapping[str,List[GlobalState]] = state_trace or {}

    def __copy__(self):
        return StateTraceAnnotation(copy(self.watch_list), copy(self.state_trace))

    def __deepcopy__(self, _):
        return StateTraceAnnotation(deepcopy(self.watch_list), deepcopy(self.state_trace)) 

def state_trace_pre_hook(global_state:GlobalState):
    opcode = global_state.get_current_instruction()['opcode']
    for annotation in global_state.get_annotations(StateTraceAnnotation):
        # 可能有有多个annotation进行追踪
        if opcode in annotation.watch_list:
            state = deepcopy(global_state)
            if opcode in annotation.state_trace:
                annotation.state_trace[opcode].append(state)
            else:
                annotation.state_trace[opcode] = [state]

def inject_state_trace(svm, global_state:GlobalState, opcodes:List[str] = None):
    global_state.annotate(StateTraceAnnotation(watch_list=opcodes))
    svm.inst_pre_hooks.append(state_trace_pre_hook)

def get_state_trace(global_state:GlobalState, opcode:str)->List[GlobalState]:
    for annotation in global_state.get_annotations(StateTraceAnnotation):
        if opcode in annotation.state_trace:
            return annotation.state_trace[opcode]
        else:
            return []
        