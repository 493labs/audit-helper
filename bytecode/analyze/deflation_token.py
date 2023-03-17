from mythril.laser.ethereum.transaction import tx_id_manager
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.laser.ethereum.state.calldata import ConcreteCalldata
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from mythril.laser.smt import Solver
solver = Solver()
import z3

from eth_utils.abi import function_signature_to_4byte_selector

from bytecode.frame.svm import SVM
from bytecode.frame.annotation.base import get_first_annotation
from bytecode.analyze.annotation.log_info import TransferLogAnnotation
from bytecode.analyze.annotation.log_info import inject_transfer_log_info
from bytecode.analyze.excepts.base import NoFinalState
from bytecode.analyze.excepts.erc20 import NoTransferLog

import logging

transfer_value = 10**12

class Complete(Exception):
    pass

def final_state_hook(final_state:GlobalState):
    annotation:TransferLogAnnotation = get_first_annotation(final_state,TransferLogAnnotation)
    if len(annotation.transfer_logs) == 0:
        raise NoTransferLog
    if len(annotation.transfer_logs) > 1:
        logging.info('一笔转账交易中触发了多次转账事件')
        raise Complete
    solver.reset()
    solver.add(annotation.transfer_logs[0].value < transfer_value)
    if solver.check() == z3.sat:
        raise Complete
    
def deflation_token_check(disassembly:Disassembly)->bool:
    
    call_data_raw = bytes().join([
        function_signature_to_4byte_selector('transfer(address,uint256)'),
        ACTORS.creator.value.to_bytes(32,'big'),
        transfer_value.to_bytes(32,'big')
    ])
    tx_id = tx_id_manager.get_next_tx_id()
    call_data = ConcreteCalldata(tx_id, call_data_raw)
    svm = SVM()
    svm.inject_final_state_hook(final_state_hook)
    try:
        final_states = svm.exec(disassembly, tx_id, call_data, inject_annotations=[inject_transfer_log_info])
    except Complete:
        return True
    if len(final_states) == 0:
        raise NoFinalState
    return False