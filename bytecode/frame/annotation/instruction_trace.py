from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from typing import List
from copy import copy, deepcopy

from bytecode.annotation.base import get_first_annotation

class InstrutionTraceAnnotation(StateAnnotation):
    def __init__(self, instrs = None):
        self.instrs:List = instrs or []

    def __copy__(self):
        return InstrutionTraceAnnotation(copy(self.instrs))

    def __deepcopy__(self, _):
        return InstrutionTraceAnnotation(deepcopy(self.instrs)) 

def instruction_trace_pre_hook(global_state:GlobalState):
    instr = global_state.get_current_instruction()
    annotation:InstrutionTraceAnnotation = get_first_annotation(global_state, InstrutionTraceAnnotation)
    if annotation:
        annotation.instrs.append(instr)

    
def inject_instruction_trace(svm, global_state:GlobalState):
    global_state.annotate(InstrutionTraceAnnotation())
    svm.inst_pre_hooks.append(instruction_trace_pre_hook)

def get_instruction_trace(global_state:GlobalState)->List:
    annotation:InstrutionTraceAnnotation = get_first_annotation(global_state, InstrutionTraceAnnotation)
    if annotation:
        return annotation.instrs
    