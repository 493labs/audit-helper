from mythril.laser.ethereum.transaction import MessageCallTransaction
from mythril.laser.ethereum.transaction.symbolic import ACTORS

from bytecode.exec import tx_exec
from bytecode.strategy.base import deploy_contract, get_world_state_with_concrete_storage
from bytecode.annotation.loop_check import *

def loop_check(deployed_code:str)->bool:
    world_state, caller_account = deploy_contract(deployed_code)
    transaction = MessageCallTransaction(
        world_state = world_state,
        gas_limit=8000000,
        origin=ACTORS.attacker,
        caller=ACTORS.attacker,
        callee_account=caller_account
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.annotate(LoopCheckAnnotation())
    try:
        tx_exec(global_state,[loop_check_pre_hook],[loop_check_post_hook],ingore_loop=False)
    except LoopSignal:
        return True
    return False

def loop_check_with_concrete_storage(code:str)->bool:
    world_state, caller_account = get_world_state_with_concrete_storage(code)
    transaction = MessageCallTransaction(
        world_state = world_state,
        gas_limit=8000000,
        origin=ACTORS.attacker,
        caller=ACTORS.attacker,
        callee_account=caller_account
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.annotate(LoopCheckAnnotation())
    try:
        tx_exec(global_state,[loop_check_pre_hook],[loop_check_post_hook],ingore_loop=False)
    except LoopSignal:
        return True
    return False
