from copy import copy, deepcopy
from typing import Mapping, List
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.state.annotation import StateAnnotation
from bytecode.frame.annotation.base import get_first_annotation

class LoopCheckAnnotation(StateAnnotation):
    def __init__(self, op_trace = None, last_pc = 0, loop_feature_ops = None):
        self.op_trace:Mapping[int,int] = op_trace or {}
        self.last_pc:int = last_pc or 0
        self.loop_feature_ops:List[int] = loop_feature_ops or []

    def __copy__(self):
        return LoopCheckAnnotation(copy(self.op_trace), copy(self.last_pc), copy(self.loop_feature_ops))

    def __deepcopy__(self, _):
        return LoopCheckAnnotation(deepcopy(self.op_trace), deepcopy(self.last_pc), deepcopy(self.loop_feature_ops))


class LoopSignal(Exception):
    pass
    
def loop_check_pre_hook(global_state: GlobalState):
    annotation:LoopCheckAnnotation = get_first_annotation(global_state,LoopCheckAnnotation)    
    if annotation:
        pc = global_state.mstate.pc
        last_pc = annotation.last_pc
        op_trace = annotation.op_trace
        loop_feature_ops = annotation.loop_feature_ops

        # 跳转到历史位置后又回到跳转点，即形成循环；正常的内部调用不会再回到跳转点
        if pc in loop_feature_ops:
            raise LoopSignal()
        
        op_trace[pc] = op_trace[pc]+1 if pc in op_trace else 1

        if global_state.get_current_instruction()['opcode'] == 'JUMPDEST' \
          and op_trace[pc] > op_trace[last_pc]:
            loop_feature_ops.append(last_pc)
        
def loop_check_post_hook(global_state: GlobalState):
    annotation:LoopCheckAnnotation = get_first_annotation(global_state,LoopCheckAnnotation)
    if annotation:
        annotation.last_pc = global_state.mstate.pc

def inject_loop_check(svm, global_state:GlobalState):
    global_state.annotate(LoopCheckAnnotation())
    svm.inst_pre_hooks.append(loop_check_pre_hook)
    svm.inst_post_hooks.append(loop_check_post_hook)