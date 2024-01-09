from typing import Mapping, List, Union, Tuple
from copy import copy, deepcopy
from enum import Enum

from slither.core.declarations import Contract, Function, SolidityVariable, SolidityVariableComposed
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
import slither.core.solidity_types as solidity_types
from slither.slithir.variables import Constant, TemporaryVariable, ReferenceVariable, TupleVariable

import z3

from ..z3_helper import check_constraints, solve_constraints, simplify
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
    Modifier = 4

class Call:
    target: SolAddress
    function_signature: str
    params: List
    call_type: CallType
    msg_sender:SolAddress
    msg_value:SolUint
    tx_origin:SolAddress 
    place_holder_point:"Call" # 用于 Modifier 场景
    master_call:"Call" # 用于 Modifier 场景
    returns:any

    def __init__(self, call_type, target, function_signature, params, msg_sender, msg_value, tx_origin):
        super().__init__()
        self.call_type = call_type
        self.target = target
        self.function_signature = function_signature
        self.params = params
        self.msg_sender = msg_sender
        self.msg_value = msg_value
        self.tx_origin = tx_origin


class MachineState(LoopState):
    wstate: WorldState
    __symbolic_vars: Mapping[str, z3.SortRef]
    __constraints: List[z3.ExprRef]

    call_stack: List[Call]
    exec_path: List[Node]
    last_call: Call
    
    def __init__(self, wstate, symbolic_vars={}, constraints=[], call_stack = [], exec_path = [], loop_stack = [], loop_reach_count = {}):
        super().__init__(loop_stack, loop_reach_count)
        self.wstate = wstate
        self.__symbolic_vars = symbolic_vars
        self.__constraints = constraints
        self.call_stack = call_stack
        self.exec_path = exec_path

    def __deepcopy__(self, _)->"MachineState":
        # 待验证deepcopy对z3的效果
        mstate = MachineState(
            deepcopy(self.wstate),
            copy(self.__symbolic_vars), 
            copy(self.__constraints), 
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
        
        elif isinstance(ir_v, (SolidityVariable, SolidityVariableComposed)):
            # 由执行环境提供
            if ir_v.name == "msg.sender":
                return self.call_stack[-1].msg_sender
            elif ir_v.name == "msg.value":
                return self.call_stack[-1].msg_value
            elif ir_v.name == "tx.origin":
                return self.call_stack[-1].tx_origin
            elif ir_v.name == "this":
                return self.call_stack[-1].target
            else:
                assert False, '未支持的类型'

        elif isinstance(ir_v, LocalVariable):
            return self.__symbolic_vars[self.get_key(ir_v)]
        
        elif isinstance(ir_v, (TemporaryVariable, ReferenceVariable, TupleVariable)):
            # 由其他类型在operation中生成
            return self.__symbolic_vars[self.get_key(ir_v)]

        else:
            assert False, '未支持的类型'

    def get_z3_var_by_key(self, key:str):
        assert isinstance(key, str)
        return self.__symbolic_vars[key]

    def set_z3_var(self, ir_v, z3_var):
        if isinstance(ir_v, StateVariable):
            self.wstate.set_storage(self.call_stack[-1].target, ir_v, z3_var)
        else:
            self.__symbolic_vars[self.get_key(ir_v)] = z3_var
    
    def get_z3_var_for_modify(self, ir_v, call:Call):
        assert isinstance(ir_v, LocalVariable)
        domain = self.get_domain(ir_v, call)
        key  = self.get_key(ir_v, domain)
        return self.__symbolic_vars[key]

    def set_z3_var_to_call_input(self, ir_v, z3_var, call:Call):
        assert isinstance(ir_v, LocalVariable)
        domain = self.get_domain(ir_v, call)
        key  = self.get_key(ir_v, domain)
        self.__symbolic_vars[key] = z3_var

    def add_constraint(self,constraint:z3.ExprRef):
        self.__constraints.append(simplify(constraint))

    def get_constraints(self):
        return self.__constraints

    def check_constraints(self):
        constraints = self.wstate.get_constraints() + self.__constraints
        return check_constraints(constraints)
    
    def solve_constraints(self):
        constraints = self.wstate.get_constraints() + self.__constraints
        return solve_constraints(constraints)


    def handle_return_ir(self, ir_v):
        self.call_stack[-1].returns = ir_v

    def handle_return(self):
        if self.exec_path[-1].type != NodeType.RETURN:
            # 方法没有显式的Return时的返回值处理
            f = self.get_cur_function()
            self.call_stack[-1].returns = f.returns

        if len(self.call_stack[-1].returns) == 1:
            # returns长度大于1时，相应的会有unpack操作，unpack中会有get_z3_var操作
            # 等于1时，在这里get_z3_var操作
            self.call_stack[-1].returns = self.get_z3_var(self.call_stack[-1].returns[0])

        self.last_call = self.call_stack.pop()

    def get_cur_function(self):
        c = self.wstate.get_contract(self.call_stack[-1].target)
        return c.get_function_from_signature(self.call_stack[-1].function_signature)