from bytecode.strategy.base import deploy_contract, get_world_state_with_concrete_storage
from bytecode.annotation.base import get_first_annotation
from bytecode.annotation.loop_check import LoopCheckAnnotation, loop_check_pre_hook, loop_check_post_hook
from bytecode.annotation.log_info import TransferLogAnnotation, transfer_log_pre_hook
from bytecode.exec import tx_exec

from mythril.laser.ethereum.state.calldata import ConcreteCalldata
from mythril.laser.ethereum.state.return_data import ReturnData
from mythril.laser.ethereum.transaction import tx_id_manager, MessageCallTransaction
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.laser.ethereum.state.world_state import WorldState,Account

from mythril.laser.smt import Concat, symbol_factory, BitVec, Solver
import z3
solver = Solver()

from eth_utils.abi import function_signature_to_4byte_selector

from typing import List
import logging

def view_func(world_state, caller_account, calldata_raw: ConcreteCalldata) -> List[ReturnData]:
    tx_id = tx_id_manager.get_next_tx_id()
    calldata = ConcreteCalldata(tx_id, calldata_raw)
    transaction = MessageCallTransaction(
        world_state = world_state,
        identifier=tx_id,
        gas_limit=8000000,
        origin=ACTORS.attacker,
        caller=ACTORS.attacker,
        callee_account=caller_account,
        call_data = calldata,
        static = True
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.annotate(LoopCheckAnnotation())
    new_global_states = tx_exec(global_state, [loop_check_pre_hook], [loop_check_post_hook])
    return [element.transaction_stack[-1][0].return_data for element in new_global_states]
    
def gene_func_sign_calldata_raw(func_sign:str)->List[BitVec]:
    func_sign = function_signature_to_4byte_selector(func_sign)
    calldata_raw = []
    for i in range(4):
        calldata_raw.append(symbol_factory.BitVecVal(func_sign[i],8))
    return calldata_raw

def deflation_token_check(deployed_code:str):
    world_state, caller_account = deploy_contract(deployed_code)

    balanceOf_calldata_raw = gene_func_sign_calldata_raw('balanceOf(address)')
    balanceOf_calldata_raw.append(ACTORS.creator)
    pre_creator_balanceOfs = view_func(world_state, caller_account, Concat(balanceOf_calldata_raw))
    balanceOf_calldata_raw = balanceOf_calldata_raw[:4]
    balanceOf_calldata_raw.append(ACTORS.attacker)
    pre_attacker_balanceOfs = view_func(world_state, caller_account, Concat(balanceOf_calldata_raw))


def deflation_token_check2(code:str)->bool:
    # world_state, caller_account = deploy_contract(deployed_code)
    world_state, caller_account = get_world_state_with_concrete_storage(code)

    # 执行交易， safemoon机制的代币存在循环问题需要处理
    transfer_value = 10**12
    call_data_raw = bytes().join([
        function_signature_to_4byte_selector('transfer(address,uint256)'),
        ACTORS.creator.value.to_bytes(32,'big'),
        transfer_value.to_bytes(32,'big')
    ])

    tx_id = tx_id_manager.get_next_tx_id()
    call_data = ConcreteCalldata(tx_id, call_data_raw)
    call_value = symbol_factory.BitVecVal(0,256)
    transaction = MessageCallTransaction(
        world_state = world_state,
        identifier=tx_id,
        gas_limit=8000000,
        origin=ACTORS.attacker,
        caller=ACTORS.attacker,
        callee_account=caller_account,
        call_data = call_data,
        call_value = call_value
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.annotate(LoopCheckAnnotation())
    global_state.annotate(TransferLogAnnotation())
    final_global_states = tx_exec(global_state, [loop_check_pre_hook, transfer_log_pre_hook], [loop_check_post_hook])
    assert len(final_global_states) > 0, '不是erc20'
    for final_global_state in final_global_states:
        annotation:TransferLogAnnotation = get_first_annotation(final_global_state, TransferLogAnnotation)
        assert len(annotation.transfer_logs) > 0, '异常的erc20实现，存在未触发Transfer事件的情况'
        if len(annotation.transfer_logs) > 1:
            logging.info('一笔转账交易中触发了多次转账事件')
            return True
        # constraint = final_global_state.world_state.constraints
        # constraint.append(annotation.transfer_logs[0].value < transfer_value)
        solver.reset()
        solver.add(*([annotation.transfer_logs[0].value < transfer_value]))
        if solver.check() == z3.sat:
            return True
    return False

    