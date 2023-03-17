from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.state.world_state import WorldState
from mythril.laser.ethereum.state.account import Account
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.laser.ethereum.transaction import TransactionStartSignal,TransactionEndSignal
from mythril.laser.ethereum.transaction import ContractCreationTransaction, MessageCallTransaction

from mythril.laser.ethereum.evm_exceptions import VmException
from mythril.laser.ethereum.instruction_data import get_required_stack_elements
from mythril.laser.ethereum.time_handler import time_handler
from mythril.disassembler.disassembly import Disassembly

from mythril.laser.smt import symbol_factory
from mythril.support.model import get_model
from mythril.exceptions import UnsatError

from typing import List, Tuple, Mapping, Callable
import logging

from bytecode.frame.instrction import Instruction
from bytecode.frame.annotation.loop_check import LoopSignal, inject_loop_check
from bytecode.frame.annotation.instruction_trace import inject_instruction_trace, get_instruction_trace
from bytecode.frame.annotation.state_trace import inject_state_trace

def get_base_world_state()->WorldState:
    world_state = WorldState()
    creator = Account(hex(ACTORS.creator.value))
    attacker = Account(hex(ACTORS.attacker.value))
    world_state.put_account(creator)
    world_state.put_account(attacker)
    return world_state

class SVM:
    def __init__(self):
        self.inst_pre_hooks:List[Callable[[GlobalState],None]] = []
        self.inst_post_hooks:List[Callable[[GlobalState],None]] = []
        self.final_state_hooks:List[Callable[[GlobalState],None]] = []
        self.tx_exec_paths:List[List] = []

    def loop_check(self, disassembly:Disassembly) -> bool:
        try:
            self.exec(disassembly, ingore_loop=False)
        except LoopSignal:
            return True
        return False

    def exec(
            self, 
            disassembly:Disassembly, 
            identifier:str = None,
            call_data = None,
            opcodes_trace:List[str] = None, 
            inject_annotations:List[Callable] = None, 
            ingore_loop:bool=True
    )->List[GlobalState]:
        world_state = get_base_world_state()
        caller_account = Account(address=symbol_factory.BitVecVal(10,256),code=disassembly)
        world_state.put_account(caller_account)
        transaction = MessageCallTransaction(
            world_state = world_state,
            identifier = identifier,
            gas_limit=8000000,
            origin=ACTORS.attacker,
            caller=ACTORS.attacker,
            callee_account=caller_account,
            call_data = call_data
        )
        start_state = transaction.initial_global_state()
        start_state.transaction_stack.append((transaction,None))

        inject_loop_check(self, start_state)
        inject_instruction_trace(self, start_state)
        inject_state_trace(self, start_state, opcodes_trace)
        for inject_annotation in inject_annotations or []:
            inject_annotation(self, start_state)
        return self.tx_exec(start_state,ingore_loop)

    def tx_exec(self, start_state: GlobalState, ingore_loop:bool=True) -> List[GlobalState]:
        states_queue = [start_state]
        states_final = []
        time_handler.start_execution(60)
        while len(states_queue) > 0:
            global_state_cur = states_queue.pop(0)

            new_states_queue, new_states_final = self.state_exec(global_state_cur, ingore_loop)
            states_final.extend(new_states_final)
            # 深度优先
            states_queue = new_states_queue + states_queue
        return states_final

    def state_exec(self, global_state_cur: GlobalState, ingore_loop:bool=True) -> Tuple[List[GlobalState], List[GlobalState]]: 
        instructions = global_state_cur.environment.code.instruction_list
        try:
            instruction = instructions[global_state_cur.mstate.pc]
        except IndexError:
            logging.warn(f'{global_state_cur.current_transaction} -> pc{global_state_cur.mstate.pc}索引越界，视为正常结束')
            return [], [global_state_cur]

        op_code = instruction['opcode']
        
        if len(global_state_cur.mstate.stack) < get_required_stack_elements(op_code):
            logging.error(f'{global_state_cur.current_transaction} -> {instruction} -> 操作码所需stack长度不足')
            return [], []

        try:
            new_global_states = Instruction(
                op_code, None, self.inst_pre_hooks, self.inst_post_hooks).evaluate(global_state_cur)
        except VmException:
            logging.error(f'{global_state_cur.current_transaction} -> {instruction} -> 虚拟机异常')
            return [], []
        except LoopSignal:
            if ingore_loop:
                logging.debug(f'{global_state_cur.current_transaction} -> {instruction} -> 出现了循环')
                return [], []
            else:
                # 用于对循环场景进行测试
                raise LoopSignal
        except TransactionStartSignal:
            logging.debug(f'{global_state_cur.current_transaction} -> {instruction} -> 出现了外部调用')
            return [], []
        except TransactionEndSignal as end_signal:
            self.tx_exec_paths.append(get_instruction_trace(end_signal.global_state))
            if not end_signal.revert:
                for final_state_hook in self.final_state_hooks:
                    final_state_hook(end_signal.global_state)
                return [], [end_signal.global_state]
            return [], []
        
        if op_code == 'JUMPI':
            new_global_states = list(filter(jumpi_filter, new_global_states))

        return new_global_states, []
    
    def inject_final_state_hook(self, final_state_hook):
        self.final_state_hooks.append(final_state_hook)

def jumpi_filter(global_state:GlobalState)->bool:
    try: 
        get_model(tuple(global_state.world_state.constraints),solver_timeout=500)
    except UnsatError:
        return False
    return True
