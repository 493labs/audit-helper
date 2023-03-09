from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.state.world_state import WorldState
from mythril.laser.ethereum.state.account import Account
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.transaction import ContractCreationTransaction, MessageCallTransaction
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.laser.smt import symbol_factory

from typing import Tuple,List,Callable

from bytecode.exec import tx_exec
from bytecode.annotation.loop_check import LoopCheckAnnotation, loop_check_pre_hook, loop_check_post_hook, LoopSignal
from bytecode.annotation.state_trace import StateTraceAnnotation, state_trace_pre_hook


def get_base_world_state()->WorldState:
    world_state = WorldState()
    creator = Account(hex(ACTORS.creator.value))
    attacker = Account(hex(ACTORS.attacker.value))
    world_state.put_account(creator)
    world_state.put_account(attacker)
    return world_state

def get_world_state_with_concrete_storage(code:str)->Tuple[WorldState, Account]:
    world_state = get_base_world_state()
    caller_account = Account(address=symbol_factory.BitVecVal(10,256),code=Disassembly(code))
    world_state.put_account(caller_account)
    return world_state, caller_account

def deploy_contract(deployed_code:str)->Tuple[WorldState, Account]:
    world_state = get_base_world_state()
    transaction = ContractCreationTransaction(
        world_state=world_state,
        gas_limit=8000000,
        origin=ACTORS.creator,
        caller=ACTORS.creator,
        code=Disassembly(deployed_code),
        call_data=None
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.world_state.constraints = []
    global_states_final = tx_exec(global_state)
    assert len(global_states_final) == 1
    return global_states_final[0].world_state, transaction.callee_account

def global_state_handle(world_state, caller_account, opcode:str, handle:Callable[[GlobalState],None])->List[GlobalState]:
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
    global_state.annotate(StateTraceAnnotation([opcode]))
    global_states_final = tx_exec(global_state,[loop_check_pre_hook,state_trace_pre_hook],[loop_check_post_hook])
    for global_state_final in global_states_final:
        for annotation in global_state_final.get_annotations(StateTraceAnnotation):
            anno:StateTraceAnnotation = annotation
            if opcode in anno.state_trace:
                for global_state_trace in anno.state_trace[opcode]:
                    handle(global_state_trace)
    return global_states_final
