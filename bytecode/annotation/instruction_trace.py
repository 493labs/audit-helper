from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from typing import List
from copy import copy, deepcopy


class InstrutionTraceAnnotation(StateAnnotation):
    def __init__(self, instrs = None):
        self.instrs:List = instrs or []

    def __copy__(self):
        return InstrutionTraceAnnotation(copy(self.instrs))

    def __deepcopy__(self, _):
        return InstrutionTraceAnnotation(deepcopy(self.instrs)) 

def instruction_trace_pre_hook(global_state:GlobalState):
    instr = global_state.get_current_instruction()
    for annotation in global_state.get_annotations(InstrutionTraceAnnotation):
        annotation.instrs.append(instr)