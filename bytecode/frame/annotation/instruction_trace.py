from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.call import get_callee_address, get_call_data
from mythril.laser.ethereum.util import get_concrete_int
from mythril.disassembler.disassembly import Disassembly
from typing import List
from copy import copy, deepcopy

from bytecode.frame.annotation.base import get_first_annotation

class InstrutionTraceAnnotation(StateAnnotation):
    def __init__(self, instrs = None, function_name = None):
        self.instrs:List = instrs or []
        self.function_name = function_name 

    def __copy__(self):
        return InstrutionTraceAnnotation(copy(self.instrs), copy(self.function_name))

    def __deepcopy__(self, _):
        return InstrutionTraceAnnotation(deepcopy(self.instrs), copy(self.function_name)) 

def instruction_trace_pre_hook(global_state:GlobalState):
    instr = global_state.get_current_instruction()
    annotation:InstrutionTraceAnnotation = get_first_annotation(global_state, InstrutionTraceAnnotation)
    if annotation:
        # 记录方法名
        disassembly:Disassembly = global_state.environment.active_account.code
        if instr['address'] in disassembly.address_to_function_name:
            function_name = disassembly.address_to_function_name[instr['address']]
            if function_name.startswith('_function_'):
                function_name = function_name[10:]
            annotation.function_name = function_name

        def set_function_name(cur_instr):
            pass
            # if annotation.function_name:
            #     cur_instr['func'] = annotation.function_name

        # 由于可能会重复赋值覆盖之前的，需要新建一个
        if instr['opcode'] in ['JUMP','JUMPI']:
            # 增加jump(i)指令的dest信息
            instr = deepcopy(instr)
            instr['dest'] = global_state.mstate.stack[-1].value
            set_function_name(instr)
        elif instr['opcode'] == 'SSTORE':
            instr = deepcopy(instr)
            instr['key'] = global_state.mstate.stack[-1].value
            instr['value'] = global_state.mstate.stack[-2].value
            set_function_name(instr)
        elif instr['opcode'] == 'SLOAD':
            instr = deepcopy(instr)
            instr['key'] = global_state.mstate.stack[-1].value
            set_function_name(instr)
        elif instr['opcode'] in ['CALL', 'STATICCALL']:
            instr = deepcopy(instr)
            to = global_state.mstate.stack[-2]
            jump = 0
            if instr['opcode'] == 'CALL':
                jump = 1
            memory_input_offset = global_state.mstate.stack[-3-jump]
            memory_input_size = global_state.mstate.stack[-4-jump]
            instr['to'] = get_callee_address(global_state, None, to)
            if memory_input_offset.symbolic or memory_input_size.symbolic:
                instr['to.func'] = 'symbolic'
            else:
                size = 4 if memory_input_size.value >= 4 else memory_input_size.value
                to_func = global_state.mstate.memory[memory_input_offset:memory_input_offset+size]
                instr['to.func'] = '0x' + bytes([get_concrete_int(item) for item in to_func]).hex()
        annotation.instrs.append(instr)

        
def inject_instruction_trace(svm, global_state:GlobalState):
    global_state.annotate(InstrutionTraceAnnotation())
    svm.add_inst_pre_hook(instruction_trace_pre_hook)

def get_instruction_trace(global_state:GlobalState)->List:
    annotation:InstrutionTraceAnnotation = get_first_annotation(global_state, InstrutionTraceAnnotation)
    if annotation:
        return annotation.instrs
    return None
    