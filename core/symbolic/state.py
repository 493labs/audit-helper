from typing import Mapping, List, Union, Tuple
from copy import copy, deepcopy
from enum import Enum

from slither.core.declarations import Contract, Function, SolidityVariable
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable
import slither.core.solidity_types as solidity_types
from slither.slithir.variables import Constant, TemporaryVariable, ReferenceVariable, TupleVariable

import z3

from .util import check_constraints

LOOP_MAX = 3

class CallType(Enum):
    Entry = 1
    Internal = 2
    External = 3

class Call:
    contract: Contract
    function: Function
    call_type: CallType
    def __init__(self,c,f,call_type) -> None:
        self.contract = c
        self.function = f
        self.call_type = call_type

class Return:
    domain: str
    vals: any
    def __init__(self, domain, vals) -> None:
        self.domain = domain
        self.vals = vals

class SymbolicState:
    __symbolic_vars: Mapping[str, z3.SortRef]
    __constraints: List[z3.ExprRef]

    __loop_stack: List[Node]
    __loop_reach_count: Mapping[Node, int]

    call_stack: List[Call]
    exec_path: List[Node]
    last_return: Return
    
    def __init__(self, symbolic_vars={}, contraists=[], call_stack = [], exec_path = []):
        self.__symbolic_vars = symbolic_vars
        self.__constraints = contraists
        self.call_stack = call_stack
        self.exec_path = exec_path

    def __deepcopy__(self)->"SymbolicState":
        # 待验证deepcopy对z3的效果
        sstate = SymbolicState(
            deepcopy(self.__symbolic_vars), 
            copy(self.__constraints), 
            copy(self.call_stack),
            copy(self.exec_path)
        )
        sstate.set_loop(copy(self.__loop_stack), copy(self.__loop_reach_count))
        return sstate
    
    def _get_z3_var(self, full_name:str, ir_v:Variable):
        # 不应该在这里构造z3变量，因为变量的来源都是方法参数
        if full_name not in self.__symbolic_vars:
            if isinstance(ir_v.type, solidity_types.ElementaryType):
                if ir_v.type.name.startswith('uint'):
                    z3_var = z3.Int(full_name)
                    self.__constraints.append(z3_var >= 0)
                elif ir_v.type.name.startswith('int'):
                    z3_var = z3.Int(full_name)
                elif ir_v.type.name == 'address':
                    # 
                    pass
                else:
                    assert False, '未处理的类型'
            # elif isinstance(ir_v.type, solidity_types.)
            else:
                assert False, '未处理的类型'

            self.__symbolic_vars[full_name] = z3_var
        return self.__symbolic_vars[full_name]

    def get_domain(self, ir_v:Variable, call:Call=None):
        if call:
            cur_call = call
        else:
            cur_call = self.call_stack[-1]
        if isinstance(ir_v, StateVariable):
            return f'{cur_call.contract.name}'
        else:
            return f'{cur_call.contract.name}.{cur_call.function.name}'
        
    def get_key(self, ir_v:Variable, domain:str = ''):
        if not domain:
            domain = self.get_domain(ir_v)
        return f'{domain}.{ir_v.name}'

    def get_z3_var(self, ir_v:Variable):
        if isinstance(ir_v, Constant):
            return ir_v.value
        
        elif isinstance(ir_v, SolidityVariable):
            # 由执行环境提供
            assert False, '未支持的类型'

        elif isinstance(ir_v, StateVariable):
            return self.__symbolic_vars[self.get_key(ir_v)]
            # return self._get_z3_var(self.get_key(ir_v), ir_v)
        elif isinstance(ir_v, LocalVariable):
            return self.__symbolic_vars[self.get_key(ir_v)]
            # return self._get_z3_var(self.get_key(ir_v), ir_v)
        
        elif isinstance(ir_v, Union[TemporaryVariable, ReferenceVariable, TupleVariable]):
            # 由其他类型在operation中生成
            return self.__symbolic_vars[self.get_key(ir_v)]

        else:
            assert False, '未支持的类型'

    def set_z3_var(self, ir_v, z3_var):
        self.__symbolic_vars[self.get_key(ir_v)] = z3_var

    def assign_z3_var(self, ir_v, ir_v_source, target_domain:str='', source_domain:str=''):
        key = self.get_key(ir_v_source, source_domain)
        assert key in self.__symbolic_vars
        self.__symbolic_vars[self.get_key(ir_v, target_domain)] = self.__symbolic_vars[key]

    def add_constraint(self, constraint):
        self.__constraints.append(constraint)

    def check_constraints(self):
        return check_constraints(self.__constraints)
    
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
    
    def set_loop(self, loop_stack, loop_reach_count):
        self.__loop_stack = loop_stack
        self.__loop_reach_count = loop_reach_count

    def set_last_return(self, ir_v):
        self.last_return = Return(self.get_domain(ir_v), ir_v)

    def call_return(self):
        call = self.call_stack.pop()
        if self.exec_path[-1].type != NodeType.RETURN:
            # 方法没有显式的Return时的返回值处理
            self.set_last_return(call.function.returns)