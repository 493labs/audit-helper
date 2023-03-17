from mythril.support.model import get_model
from mythril.exceptions import UnsatError
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.state.world_state import WorldState
from mythril.laser.ethereum.state.account import Account
from mythril.laser.ethereum.transaction import (
    ContractCreationTransaction, 
    MessageCallTransaction,
    TransactionStartSignal,
    TransactionEndSignal
)
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.laser.ethereum.evm_exceptions import VmException
from mythril.laser.ethereum.instruction_data import get_required_stack_elements
from mythril.laser.smt import symbol_factory

from typing import Tuple,List,Callable
import logging

from bytecode.frame.instrction import Instruction
from bytecode.frame.annotation.loop_check import LoopCheckAnnotation, loop_check_pre_hook, loop_check_post_hook
from bytecode.frame.annotation.state_trace import StateTraceAnnotation, state_trace_pre_hook
from bytecode.frame.annotation.loop_check import LoopSignal

def jumpi_filter(global_state:GlobalState)->bool:
    try: 
        get_model(tuple(global_state.world_state.constraints),solver_timeout=500)
    except UnsatError:
        return False
    return True

def state_exec(
        global_state_cur: GlobalState, 
        pre_hooks: List[Callable]=None, 
        post_hooks: List[Callable]=None, 
        ingore_loop:bool=True,
        ) -> Tuple[List[GlobalState], List[GlobalState], Instruction]: 
    instructions = global_state_cur.environment.code.instruction_list
    try:
        instruction = instructions[global_state_cur.mstate.pc]
    except IndexError:
        logging.warn(f'{global_state_cur.current_transaction} -> pc{global_state_cur.mstate.pc}索引越界，视为正常结束')
        return [], [global_state_cur], None

    op_code = instruction['opcode']
    
    if len(global_state_cur.mstate.stack) < get_required_stack_elements(op_code):
        logging.error(f'{global_state_cur.current_transaction} -> {instruction} -> 操作码所需stack长度不足')
        return [], [], instruction

    try:
        new_global_states = Instruction(
            op_code, None, pre_hooks, post_hooks).evaluate(global_state_cur)
        
    except VmException:
        logging.error(f'{global_state_cur.current_transaction} -> {instruction} -> 虚拟机异常')
        return [], [], instruction
    except LoopSignal:
        if ingore_loop:
            logging.debug(f'{global_state_cur.current_transaction} -> {instruction} -> 出现了循环')
            return [], [], instruction
        else:
            # 用于对循环场景进行测试
            raise LoopSignal
    except TransactionStartSignal:
        logging.debug(f'{global_state_cur.current_transaction} -> {instruction} -> 出现了外部调用')
        return [], [], instruction
    except TransactionEndSignal as end_signal:
        if not end_signal.revert:
            return [], [end_signal.global_state], instruction
        return [], [], instruction
    
    if op_code == 'JUMPI':
        new_global_states = list(filter(jumpi_filter, new_global_states))

    return new_global_states, [], instruction

def tx_exec(start_state: GlobalState, pre_hooks: List[Callable]=None, post_hooks: List[Callable]=None, ingore_loop:bool=True) -> List[GlobalState]:
    states_queue = [start_state]
    states_final = []
    # cfg = CFG
    while len(states_queue) > 0:
        global_state_cur = states_queue.pop(0)
        # cfg.add_inst(global_state_cur)

        new_states_queue, new_states_final, _ = state_exec(global_state_cur, pre_hooks, post_hooks, ingore_loop)
        states_final.extend(new_states_final)
        # 深度优先
        states_queue = new_states_queue + states_queue
    return states_final


def get_base_world_state()->WorldState:
    world_state = WorldState()
    creator = Account(hex(ACTORS.creator.value))
    attacker = Account(hex(ACTORS.attacker.value))
    world_state.put_account(creator)
    world_state.put_account(attacker)
    return world_state


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

class Temp(Exception):
    pass

def _arbitrary_write_handler(global_state_trace:GlobalState):
    constraints = global_state_trace.world_state.constraints
    constraints.append(global_state_trace.mstate.stack[-1]==0)
    try:
        model = get_model(tuple(constraints), enforce_execution_time = False)
        raise Temp
    except UnsatError as e:
        pass

def arbitrary_write_check(deployed_code:str)->bool:
    world_state, caller_account = deploy_contract(deployed_code)
    try:
        global_states_final = global_state_handle(world_state,caller_account,'SSTORE',_arbitrary_write_handler)
        for global_state_final in global_states_final:
            global_state_handle(global_state_final.world_state, caller_account, 'SSTORE', _arbitrary_write_handler)
    except Temp:
        return True
    return False
