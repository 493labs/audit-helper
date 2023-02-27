from copy import copy, deepcopy
from typing import Mapping
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.state.annotation import StateAnnotation

class LoopCheckAnnotation(StateAnnotation):
    def __init__(self, op_trace = None):
        self.op_trace:Mapping[int,int] = op_trace or {}

    def __copy__(self):
        return LoopCheckAnnotation(copy(self.op_trace))

    def __deepcopy__(self, _):
        return LoopCheckAnnotation(deepcopy(self.op_trace))


class LoopSignal(Exception):
    pass


def get_loop_check_annotation(global_state:GlobalState)->LoopCheckAnnotation:
    for annotation in global_state.annotations:
        if isinstance(annotation, LoopCheckAnnotation):
            return annotation # 只返回第一个，约定只有一个该对象
    return None
    
def loop_check_pre_hook(global_state: GlobalState):
    loop_check_annotation = get_loop_check_annotation(global_state)
    if loop_check_annotation:
        pc = global_state.mstate.pc
        if pc in loop_check_annotation.op_trace:
            loop_check_annotation.op_trace[pc] += 1
        else:
            loop_check_annotation.op_trace[pc] = 1

        if loop_check_annotation.op_trace[pc] > 6:
            raise LoopSignal()