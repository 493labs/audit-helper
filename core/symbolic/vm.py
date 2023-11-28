from typing import Mapping, List, Tuple
from copy import deepcopy
from enum import Enum

from slither.core.declarations import Contract, Function
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.variable import Variable
import slither.slithir.operations as operations

from .state import SymbolicState, LOOP_MAX, CallType, Call, Return

import z3

class Environment:
    # address_to_contract: Mapping[str, Contract]
    # name_to_contract: Mapping[str, Contract]
    # interface_to_contract: Mapping[str, Contract]
    # symbolic_states: List[SymbolicState]
    contract: Contract
    function: Function


class ExecVM:
    symbolic_state_checks: Mapping[SymbolicState, bool] = {}    

    def exec_ir(self, sstate:SymbolicState, ir:operations.Operation):
        if isinstance(ir, operations.Binary):
            left_value_z3 = sstate.get_z3_var(ir.variable_left)
            right_value_z3 = sstate.get_z3_var(ir.variable_right)
            if ir.type == operations.BinaryType.ADDITION:
                lvalue_z3 = left_value_z3 + right_value_z3
            elif ir.type == operations.BinaryType.GREATER:
                lvalue_z3 = left_value_z3 > right_value_z3
            elif ir.type == operations.BinaryType.GREATER_EQUAL:
                lvalue_z3 = left_value_z3 >= right_value_z3
            else:
                assert False, '未处理的二元操作'
            sstate.set_z3_var(ir.lvalue, lvalue_z3)

        elif isinstance(ir, operations.Assignment):
            sstate.assign_z3_var(ir.lvalue, ir.rvalue)

        elif isinstance(ir, operations.SolidityCall):
            if ir.function.name.startswith('require'):
                sstate.add_constraint(sstate.get_z3_var(ir.arguments[0]))
            else:
                assert False, '未处理的 solidity call'

        elif isinstance(ir, operations.InternalCall):
            # 需要更新输入参数的值，而方法里的变量会重新赋值
            if isinstance(ir.function, Function):
                count = len(ir.function.return_type.parameters)
                assert count == len(ir.nbr_arguments)
                contract = sstate.call_stack[-1].contract
                for i in range(count):
                    target_domain = f'{contract.name}.{ir.function.name}'
                    sstate.assign_z3_var(ir.function.parameters[i], ir.nbr_arguments[i],target_domain)
                self.exec(contract, ir.function,CallType.Internal,False,sstate)
                # 待进一步完善，与unpack结合，需要反思reference、tuple、执行环境的情况
                ir.lvalue = sstate.last_return
            else:
                assert False, '未处理的 internal call'

        elif isinstance(ir, operations.HighLevelCall):
            # 与InternalCall的情况其实类似
            pass

        elif isinstance(ir, operations.Return):
            sstate.set_last_return(ir.values)

        elif isinstance(ir, operations.Unpack):
            pass

        else:
            assert False, '未处理的ir'

    def add_if_cond_and_travel(self, sstate:SymbolicState, node: Node, if_true: bool, is_loop:bool=False):
        assert node.type == NodeType.IFLOOP if is_loop else NodeType.IF
        for ir in node.irs:
            if isinstance(ir, operations.Condition):
                if if_true:
                    sstate.__constraints.append(ir.value)
                else:
                    sstate.__constraints.append(z3.Not(ir.value))

                if sstate.check_constraints():
                    if is_loop and not if_true:
                        sstate.loop_pop()
                    son_node = node.son_true if if_true else node.son_false
                    self.travel(sstate, son_node)
                else:
                    self.symbolic_state_checks[sstate] = False

    def travel(self, sstate:SymbolicState, node:Node):
        sstate.exec_path.append(node)
        for ir in node.irs:
            self.exec_ir(sstate, ir)
        
        if node.type == NodeType.IF:
            sstate_if_false = deepcopy(sstate)
            self.symbolic_state_checks[sstate_if_false] = True

            self.add_if_cond_and_travel(sstate, node, True)
            self.add_if_cond_and_travel(sstate_if_false, node, False)

        elif node.type == NodeType.IFLOOP:
            sstate.loop_push(node)

            sstate_if_false = deepcopy(sstate)
            self.symbolic_state_checks[sstate_if_false] = True

            if sstate.get_loop_reach_count(node) <= LOOP_MAX :
                self.add_if_cond_and_travel(sstate, node, True, is_loop=True)
            self.add_if_cond_and_travel(sstate_if_false, node, False, is_loop=True)

        else:
            if node.sons:
                self.travel(sstate, node.sons[0])
            else:
                sstate.call_return()

    def exec(self, c:Contract, f: Function, call_type:CallType=CallType.Entry, is_entry:bool=True, sstate:SymbolicState = None):
        if is_entry:
            sstate = SymbolicState()
            self.symbolic_state_checks[sstate] = True
        sstate.call_stack.append(
            Call(c,f,call_type)
        )
        self.travel(sstate, f.entry_point)
        
        
