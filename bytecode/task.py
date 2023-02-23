from mythril.disassembler.disassembly import Disassembly
from mythril.laser.ethereum.state.world_state import WorldState
from mythril.laser.ethereum.state.account import Account
from mythril.laser.ethereum.state.calldata import SymbolicCalldata
from mythril.laser.ethereum.state.global_state import GlobalState
from mythril.laser.ethereum.transaction import (
    MessageCallTransaction,
    ContractCreationTransaction,
    tx_id_manager,
)
from mythril.laser.ethereum.cfg import Node

from mythril.laser.smt import symbol_factory, simplify
from mythril.laser.smt.bitvec_helper import Concat

import logging
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO,format=LOG_FORMAT)
from typing import Tuple,List
import sys,os
sys.path.append('.')
from bytecode.exec import exec, gene_calldata_contraints
from bytecode.strategy.loop_check import LoopCheckAnnotation, loop_check_pre_hook
from bytecode.strategy.state_trace import StateTraceAnnotation, state_trace_pre_hook

from mythril.support.model import get_model
from mythril.laser.smt import Solver
solver = Solver()
from mythril.solidity.soliditycontract import SolidityContract
from mythril.laser.ethereum.transaction.symbolic import ACTORS
from mythril.exceptions import UnsatError, SolverTimeOutException

from core.utils.change_solc_version import change_solc_version

def get_contract(solc_dir:str, contract_path:str, contract_name:str=None)->SolidityContract:
    if solc_dir and len(solc_dir) > 0:
        cur_dir = os.getcwd()
        os.chdir(solc_dir)
        change_solc_version(contract_path)
        contract = SolidityContract(contract_path, contract_name)
        os.chdir(cur_dir)
    else:
        change_solc_version(contract_path)
        contract = SolidityContract(contract_path, contract_name)
    return contract

def deploy_contract(world_state:WorldState, deployed_code:str)->Tuple[Account,List[GlobalState]]:
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
    # global_state.annotate(LoopCheckAnnotation())
    # global_states_final = exec(global_state,[loop_check_pre_hook])
    global_states_final = exec(global_state)
    return transaction.callee_account,global_states_final

def arbitrary_write_attack(world_state:WorldState,caller_account:Account)->List[GlobalState]:
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
    # SHA3
    global_state.annotate(StateTraceAnnotation(['SSTORE']))
    global_states_final = exec(global_state,[loop_check_pre_hook, state_trace_pre_hook])
    ret = []
    for global_state_final in global_states_final:
        has_sstore, global_states_trace = has_opcode_and_get_state(global_state_final,'SSTORE')
        if has_sstore:
            ret.append(global_state_final)
            for global_state_trace in global_states_trace:
                constraints = global_state_trace.world_state.constraints
                constraints.append(global_state_trace.mstate.stack[-1]==0)
                # solver.reset()
                # solver.add(*(constraints))
                # is_sat = solver.check()
                try:
                    model = get_model(tuple(constraints), enforce_execution_time = False)
                    print(global_state_trace.get_current_instruction())
                except UnsatError as e:
                    pass
    return ret

def has_opcode_and_get_state(global_state:GlobalState, opcode:str)->Tuple[bool,List[GlobalState]]:
    # 判断时，暂不考虑外部调用中存在sstore的情况
    for annotation in global_state.get_annotations(StateTraceAnnotation):
        anno:StateTraceAnnotation = annotation
        if opcode in anno.state_trace:
            return True, anno.state_trace[opcode]
        else:
            return False, None

def overflow_check(world_state:WorldState,caller_account:Account):
    transaction = MessageCallTransaction(
        world_state = world_state,
        gas_limit=8000000,
        origin=ACTORS.attacker,
        caller=ACTORS.attacker,
        callee_account=caller_account
    )
    global_state = transaction.initial_global_state()
    global_state.transaction_stack.append((transaction,None))
    global_state.annotate(StateTraceAnnotation(['SUB']))
    global_states_final = exec(global_state,[state_trace_pre_hook])
    for global_state_final in global_states_final:
        has_sub, global_states_trace = has_opcode_and_get_state(global_state_final, 'SUB')
        if has_sub:
            for global_state_trace in global_states_trace:
                constraints = global_state_trace.world_state.constraints
                constraints.append(global_state_trace.mstate.stack[-1]<global_state_trace.mstate.stack[-2])
                try:
                    model = get_model(tuple(constraints), enforce_execution_time = False)
                    print(global_state_trace.get_current_instruction())
                except UnsatError as e:
                    pass


if __name__ == "__main__":
    # with open('test/data/bytecode/1','r') as fp:
    #     code = fp.read() 
    # disassembly = Disassembly(code)
    solidity_contract = get_contract(None, './test/data/sol/MerdeToken.sol','MerdeToken')

    world_state = WorldState()
    creator = Account(hex(ACTORS.creator.value))
    attacker = Account(hex(ACTORS.attacker.value))
    world_state.put_account(creator)
    world_state.put_account(attacker)

    # 以 world state 为核心，发送3笔交易
    contract, global_states = deploy_contract(world_state,solidity_contract.creation_code)
    # global_states2 = arbitrary_write_attack(global_states[0].world_state,contract)
    # for global_state in global_states2:
    #     arbitrary_write_attack(global_state.world_state,contract)
    overflow_check(global_states[0].world_state,contract)

    

    # transfer(address,uint256) 0xa9059cbb
    # transfer_func_hash = symbol_factory.BitVecVal(int('0xa9059cbb',16),32)
    # call_data = Concat([transfer_func_hash, external_sender, transfer_value])

    # next_transaction_id = tx_id_manager.get_next_tx_id()
    # call_data = SymbolicCalldata(next_transaction_id)
    # transaction = MessageCallTransaction(
    #     world_state = world_state,
    #     identifier = next_transaction_id,
    #     gas_limit = 8000000,
    #     origin = external_sender,
    #     caller = external_sender,
    #     callee_account = world_state[contract_addr],
    #     call_data = call_data
    # )
    
    # global_state = transaction.initial_global_state()
    # global_state.transaction_stack.append((transaction, None))
    # global_state.world_state.constraints = gene_calldata_contraints(
    #     call_data, 'transfer(address,uint256)'
    # )

    # new_node = Node(
    #     global_state.environment.active_account.contract_name,
    #     function_name=global_state.environment.active_function_name,
    # )

    # global_state.world_state.transaction_sequence.append(transaction)
    # global_state.node = new_node
    # new_node.states.append(global_state)

    # states_final = exec(global_state)
    # # back_track(states_final[0])
    # if states_final:
    #     print(states_final,states_final[0].mstate.min_gas_used, states_final[0].mstate.max_gas_used)

    # from eth_utils.abi import function_signature_to_4byte_selector
    # func_hash = function_signature_to_4byte_selector('transfer(address,uint256)').hex()
    # print(func_hash)

