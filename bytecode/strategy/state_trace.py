from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from typing import List, Mapping
from copy import copy, deepcopy


class StateTraceAnnotation(StateAnnotation):
    def __init__(self, watch_list = None, state_trace = None):
        self.watch_list:List[str] = watch_list or {}
        self.state_trace:Mapping[str,List[GlobalState]] = state_trace or {}

    def __copy__(self):
        return StateTraceAnnotation(copy(self.watch_list), copy(self.state_trace))

    def __deepcopy__(self, _):
        return StateTraceAnnotation(deepcopy(self.watch_list), deepcopy(self.state_trace)) 

def state_trace_pre_hook(global_state:GlobalState):
    opcode = global_state.get_current_instruction()['opcode']
    for annotation in global_state.get_annotations(StateTraceAnnotation):
        if opcode in annotation.watch_list:
            state = deepcopy(global_state)
            if opcode in annotation.state_trace:
                annotation.state_trace[opcode].append(state)
            else:
                annotation.state_trace[opcode] = [state]