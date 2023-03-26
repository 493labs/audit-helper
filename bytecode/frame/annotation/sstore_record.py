from mythril.laser.ethereum.state.annotation import StateAnnotation
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.smt import BitVec
from typing import List, Mapping, Optional
from copy import copy, deepcopy
from .base import get_first_annotation

class SstoreRecordAnnotation(StateAnnotation):
    def __init__(self, store_records = None) -> None:
        self.store_records:Mapping[int, Mapping[BitVec, BitVec]] = store_records or {}
    
    def __copy__(self):
        return SstoreRecordAnnotation(copy(self.store_records))

    def __deepcopy__(self, _):
        return SstoreRecordAnnotation(deepcopy(self.store_records)) 


    pass
    # 记录sstore信息，多笔交易的线性模式和指数模式

def sstore_record_pre_hook(global_state:GlobalState):
    inst = global_state.get_current_instruction()
    if inst['opcode'] != 'SSTORE':
        return
    annotation:SstoreRecordAnnotation = get_first_annotation(global_state, SstoreRecordAnnotation)
    if not annotation:
        return
    caller_address = global_state.environment.active_account.address
    key, value = deepcopy(global_state.mstate.stack[-1]) , deepcopy(global_state.mstate.stack[-2])
    if caller_address not in annotation.store_records:
        annotation.store_records[caller_address] = {}
    annotation.store_records[caller_address][key] = value

def inject_sstore_record(svm, global_state:GlobalState):
    global_state.annotate(SstoreRecordAnnotation())
    svm.add_inst_pre_hook(sstore_record_pre_hook)

def get_sstore_records(global_state:GlobalState) -> Optional[Mapping[int, Mapping[BitVec, BitVec]]]:
    innotation: SstoreRecordAnnotation = get_first_annotation(global_state, SstoreRecordAnnotation)
    if not innotation:
        return None
    return innotation.store_records