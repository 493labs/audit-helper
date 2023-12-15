from typing import Mapping, List, Union, Tuple
from copy import copy, deepcopy
from enum import Enum

from slither.core.declarations import Contract, Function, SolidityVariableComposed
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
import slither.core.solidity_types as solidity_types
from slither.slithir.variables import Constant, TemporaryVariable, ReferenceVariable, TupleVariable

import z3

from ..z3_helper import check_constraints, solve_constraints
from ..types import SolAddress, SolUint
from .world_state import WorldState

LOOP_MAX = 3

class LoopState:
    __loop_stack: List[Node]
    __loop_reach_count: Mapping[Node, int]

    def __init__(self, loop_stack=[], loop_reach_count={}) -> None:
        self.__loop_stack = loop_stack
        self.__loop_reach_count = loop_reach_count

    def loop_push(self, node: Node):
        assert node.type == NodeType.IFLOOP
        if self.__loop_stack:
            last_loop_node = self.__loop_stack[-1]
            if node == last_loop_node:
                self.__loop_reach_count[node] +=1
            else:
                self.__loop_stack.append(node)
                self.__loop_reach_count[node] = 1
        else:
            self.__loop_stack = [node]
            self.__loop_reach_count = {node:1}
    
    def loop_pop(self):
        assert self.__loop_stack
        node = self.__loop_stack.pop()
        # 避免多次内部调用中的循环时相互干扰
        del self.__loop_reach_count[node]

    def get_loop_reach_count(self, node:Node):
        assert node in self.__loop_reach_count
        return self.__loop_reach_count[node]
    
    # def set_loop(self, loop_stack, loop_reach_count):
    #     self.__loop_stack = loop_stack
    #     self.__loop_reach_count = loop_reach_count

    def copy_loop_stack(self):
        return copy(self.__loop_stack)
    
    def copy_loop_reach_count(self):
        return copy(self.__loop_reach_count)

class CallType(Enum):
    Entry = 1
    Internal = 2
    External = 3

class Call:
    target: SolAddress
    function_signature: str
    params: List
    call_type: CallType
    msg_sender:SolAddress
    msg_value:SolUint
    tx_origin:SolAddress 

    def __init__(self, call_type, target, function_signature, params, msg_sender, msg_value, tx_origin):
        super().__init__()
        self.call_type = call_type
        self.target = target
        self.function_signature = function_signature
        self.params = params
        self.msg_sender = msg_sender
        self.msg_value = msg_value
        self.tx_origin = tx_origin

class Return:
    the_call: Call
    vals: any
    def __init__(self, the_call, vals) -> None:
        self.the_call = the_call
        self.vals = vals

class MachineState(LoopState):
    wstate: WorldState
    __symbolic_vars: Mapping[str, z3.SortRef]
    constraints: List[z3.ExprRef]

    call_stack: List[Call]
    exec_path: List[Node]
    last_return: Return
    
    def __init__(self, wstate, symbolic_vars={}, constraints=[], call_stack = [], exec_path = [], loop_stack = [], loop_reach_count = {}):
        super().__init__(loop_stack, loop_reach_count)
        self.wstate = wstate
        self.__symbolic_vars = symbolic_vars
        self.constraints = constraints
        self.call_stack = call_stack
        self.exec_path = exec_path

    def __deepcopy__(self, _)->"MachineState":
        # 待验证deepcopy对z3的效果
        mstate = MachineState(
            deepcopy(self.wstate),
            copy(self.__symbolic_vars), 
            copy(self.constraints), 
            copy(self.call_stack),
            copy(self.exec_path),
            super().copy_loop_stack(),
            super().copy_loop_reach_count
        )
        return mstate

    
    def get_domain(self, ir_v:Variable, call:Call=None):
        if call:
            cur_call = call
        else:
            cur_call = self.call_stack[-1]
        if isinstance(ir_v, StateVariable):
            return self.wstate.get_domain(cur_call.target)
        else:
            return f'mstate.{cur_call.target}.{ir_v.function.full_name}'
        
    def get_key(self, ir_v:Variable, domain:str = ''):
        if not domain:
            domain = self.get_domain(ir_v)
        return f'{domain}.{ir_v.name}'

    def get_z3_var(self, ir_v:Variable):
        if isinstance(ir_v, Constant):
            return ir_v.value
        
        elif isinstance(ir_v, StateVariable):
            return self.wstate.get_storage(self.call_stack[-1].target, ir_v)
        
        elif isinstance(ir_v, SolidityVariableComposed):
            # 由执行环境提供
            if ir_v.name == "msg.sender":
                return self.call_stack[-1].msg_sender
            elif ir_v.name == "msg.value":
                return self.call_stack[-1].msg_value
            elif ir_v.name == "tx.origin":
                return self.call_stack[-1].tx_origin
            else:
                assert False, '未支持的类型'

        elif isinstance(ir_v, LocalVariable):
            return self.__symbolic_vars[self.get_key(ir_v)]
        
        elif isinstance(ir_v, Union[TemporaryVariable, ReferenceVariable, TupleVariable]):
            # 由其他类型在operation中生成
            return self.__symbolic_vars[self.get_key(ir_v)]

        else:
            assert False, '未支持的类型'

    def set_z3_var(self, ir_v, z3_var):
        if isinstance(ir_v, StateVariable):
            self.wstate.accounts[self.call_stack[-1].target].set_storage(ir_v,z3_var)
        else:
            self.__symbolic_vars[self.get_key(ir_v)] = z3_var

    def check_constraints(self):
        constraints = self.wstate.get_constraints() + self.constraints
        return check_constraints(constraints)
    
    def solve_constraints(self):
        constraints = self.wstate.get_constraints() + self.constraints
        return solve_constraints(constraints)


    def set_last_return(self, ir_v):
        self.last_return = Return(self.call_stack[-1].function_signature, ir_v)

    def call_return(self):
        f = self.get_cur_function()
        if self.exec_path[-1].type != NodeType.RETURN:
            # 方法没有显式的Return时的返回值处理
            self.set_last_return(f.returns)
        self.call_stack.pop()

    def get_cur_function(self):
        c = self.wstate.get_contract(self.call_stack[-1].target)
        return c.get_function_from_signature(self.call_stack[-1].function_signature)