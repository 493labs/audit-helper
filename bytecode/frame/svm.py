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

from mythril.laser.smt import symbol_factory, Bool, Or, And
from mythril.support.model import get_model
from mythril.exceptions import UnsatError

from typing import List, Tuple, Mapping, Callable
import logging
from copy import copy, deepcopy

from bytecode.frame.instrction import Instruction
from bytecode.frame.annotation.loop_check import LoopSignal, inject_loop_check
from bytecode.frame.annotation.instruction_trace import inject_instruction_trace, get_instruction_trace
from bytecode.frame.annotation.state_trace import inject_state_trace
from .annotation.sstore_record import inject_sstore_record, get_sstore_records

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
            concrete_storage: bool = False,
            identifier:str = None,
            transaction_count:int = 1,
            call_data = None,
            init_constraints = None,
            opcodes_trace:List[str] = None, 
            inject_annotations:List[Callable] = None, 
            ingore_loop:bool=True
    ) -> List[GlobalState]:
        world_state = get_base_world_state()
        caller_account = Account(address=symbol_factory.BitVecVal(10,256), code=disassembly, concrete_storage=concrete_storage)
        world_state.put_account(caller_account)

        open_states = [world_state]
        final_global_states = []
        for _ in range(transaction_count):
            temp_open_states = open_states
            open_states = []
            for open_state in temp_open_states:          
                transaction = MessageCallTransaction(
                    world_state = deepcopy(open_state),
                    identifier = identifier,
                    gas_limit=8000000,
                    origin=ACTORS.attacker,
                    caller=ACTORS.attacker,
                    callee_account=caller_account,
                    call_data = call_data
                )
                start_state = transaction.initial_global_state()
                start_state.transaction_stack.append((transaction,None))
                if init_constraints:
                    start_state.world_state.constraints = init_constraints

                inject_loop_check(self, start_state)
                inject_instruction_trace(self, start_state)
                inject_state_trace(self, start_state, opcodes_trace)
                for inject_annotation in inject_annotations or []:
                    inject_annotation(self, start_state)
                step_global_states = self.tx_exec(start_state,ingore_loop)
                open_states.extend([global_state.world_state for global_state in step_global_states])
                final_global_states.extend(step_global_states)
        return final_global_states
    
    def exec_liner(
            self, 
            disassembly:Disassembly, 
            concrete_storage: bool = True,
            # identifier:str = None,
            # transaction_count:int = 2,
            # call_data = None,
            # init_constraints = None,
            opcodes_trace:List[str] = None, 
            inject_annotations:List[Callable] = None, 
            ingore_loop:bool=True
    ) -> List[GlobalState]:
        world_state = get_base_world_state()
        caller_account = Account(address=symbol_factory.BitVecVal(10,256), code=disassembly, concrete_storage=concrete_storage)
        world_state.put_account(caller_account)

        final_global_states = []
        # 限定两次交易，线性模式无法处理超过两次交易的情况
        for _ in range(2): 
            open_state = deepcopy(world_state) 
            transaction = MessageCallTransaction(
                world_state = open_state,
                # identifier = identifier,
                gas_limit=8000000,
                origin=ACTORS.attacker,
                caller=ACTORS.attacker,
                callee_account=caller_account,
                # call_data = call_data
            )
            start_state = transaction.initial_global_state()
            start_state.transaction_stack.append((transaction,None))

            or_contraints = Bool(False)
            need_the_contraints = False
            for final_global_state in final_global_states:
                sstore_records = get_sstore_records(final_global_state) 
                if not sstore_records:
                    continue
                if not need_the_contraints:
                    need_the_contraints = True

                and_contraint = Bool(True)
                for address, key_values in sstore_records.items():
                    accout = open_state.accounts_exist_or_load(address,None)
                    for key, value in key_values.items():
                        assert not key.symbolic
                        if key not in accout.storage.keys_set:
                            accout.storage[key] = symbol_factory.BitVecSym(f'storage_{address}_{key.value}',256)
                        and_contraint = And(and_contraint,accout.storage[key] == value)
                or_contraints = Or(or_contraints, and_contraint)
            if need_the_contraints:
                start_state.world_state.constraints.append(or_contraints)

            inject_loop_check(self, start_state)
            inject_instruction_trace(self, start_state)
            inject_state_trace(self, start_state, opcodes_trace)
            inject_sstore_record(self, start_state)
            for inject_annotation in inject_annotations or []:
                inject_annotation(self, start_state)
            # 只针对两次交易的情况
            final_global_states.extend(self.tx_exec(start_state,ingore_loop))
        return final_global_states

    def tx_exec(self, start_state: GlobalState, ingore_loop:bool=True) -> List[GlobalState]:
        states_queue = [start_state]
        states_final = []
        time_handler.start_execution(100)
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
            logging.info(f'{global_state_cur.current_transaction} -> {instruction} -> 出现了外部调用')
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
    
    def add_inst_pre_hook(self, inst_pre_hook:Callable[[GlobalState],None]):
        if inst_pre_hook not in self.inst_pre_hooks:
            self.inst_pre_hooks.append(inst_pre_hook)
    def add_inst_post_hook(self, inst_post_hook:Callable[[GlobalState],None]):
        if inst_post_hook not in self.inst_post_hooks:
            self.inst_post_hooks.append(inst_post_hook)
    def inject_final_state_hook(self, final_state_hook:Callable[[GlobalState],None]):
        if final_state_hook not in self.final_state_hooks:
            self.final_state_hooks.append(final_state_hook)

def jumpi_filter(global_state:GlobalState)->bool:
    try: 
        get_model(tuple(global_state.world_state.constraints),solver_timeout=500)
    except UnsatError:
        return False
    return True
