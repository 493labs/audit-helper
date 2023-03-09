from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState

from mythril.laser.smt import BitVec

from typing import List
from copy import copy, deepcopy

from eth_utils.crypto import keccak

from bytecode.annotation.base import get_first_annotation

# event Transfer(address indexed from, address indexed to, uint256 value);
TOP0 = keccak(text='Transfer(address,address,uint256)')

class TransferLog:
    def __init__(self, sender=None, receiver=None, value=0):
        self.sender = sender
        self.receiver = receiver
        self.value = value

    def __copy__(self):
        return TransferLog(copy(self.sender),copy(self.receiver),copy(self.value))

    def __deepcopy__(self, _):
        return TransferLog(deepcopy(self.sender),deepcopy(self.receiver),deepcopy(self.value))
    
class TransferLogAnnotation(StateAnnotation):
    def __init__(self, transfer_logs:List[TransferLog] = None):
        self.transfer_logs = transfer_logs or []

    def __copy__(self):
        return TransferLogAnnotation(copy(self.transfer_logs))

    def __deepcopy__(self, _):
        return TransferLogAnnotation(deepcopy(self.transfer_logs))
    
def transfer_log_pre_hook(global_state:GlobalState):
    op_code:str = global_state.get_current_instruction()['opcode']
    if op_code.startswith('LOG'):
        depth = int(op_code[3:])
        stack = global_state.mstate.stack
        offset, length = stack[-1], stack[-2]
        top0:BitVec = stack[-3]
        if top0.value == int.from_bytes(TOP0,'big'):
            assert depth == 3 and length.value == 32
            transfer_log = TransferLog(stack[-4], stack[-5], global_state.mstate.memory.get_word_at(offset))
            annotation:TransferLogAnnotation = get_first_annotation(global_state, TransferLogAnnotation)
            annotation.transfer_logs.append(transfer_log)
