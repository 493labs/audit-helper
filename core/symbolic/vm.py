from typing import Mapping, List, Tuple
from copy import deepcopy, copy
from enum import Enum

from slither.core.declarations import Contract, Function
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.variable import Variable
import slither.slithir.operations as operations

from .state.machine_state import MachineState, LOOP_MAX, CallType, Call, Return
from .state.world_state import WorldState

import z3

class ExecVM:

    mstate_check_constraints: Mapping[MachineState, bool] = {}    

    def exec_ir(self, mstate:MachineState, ir:operations.Operation):
        if isinstance(ir, operations.Binary):
            left_value_z3 = mstate.get_z3_var(ir.variable_left)
            right_value_z3 = mstate.get_z3_var(ir.variable_right)
            if ir.type == operations.BinaryType.ADDITION:
                lvalue_z3 = left_value_z3 + right_value_z3
            elif ir.type == operations.BinaryType.SUBTRACTION:
                lvalue_z3 = left_value_z3 - right_value_z3
            elif ir.type == operations.BinaryType.POWER:
                lvalue_z3 = left_value_z3 ** right_value_z3
            elif ir.type == operations.BinaryType.GREATER:
                lvalue_z3 = left_value_z3 > right_value_z3
            elif ir.type == operations.BinaryType.GREATER_EQUAL:
                lvalue_z3 = left_value_z3 >= right_value_z3
            elif ir.type == operations.BinaryType.LESS:
                lvalue_z3 = left_value_z3 < right_value_z3
            elif ir.type == operations.BinaryType.LESS_EQUAL:
                lvalue_z3 = left_value_z3 <= right_value_z3
            elif ir.type == operations.BinaryType.OROR:
                lvalue_z3 = z3.Or(left_value_z3, right_value_z3)
            elif ir.type == operations.BinaryType.ANDAND:
                lvalue_z3 = z3.And(left_value_z3, right_value_z3)
            elif ir.type == operations.BinaryType.NOT_EQUAL:
                lvalue_z3 = left_value_z3 != right_value_z3
            else:
                assert False, '未处理的二元操作'
            mstate.set_z3_var(ir.lvalue, lvalue_z3)

        elif isinstance(ir, operations.Assignment):
            v = mstate.get_z3_var(ir.rvalue)
            mstate.set_z3_var(ir.lvalue, v)

        # elif isinstance(ir, operations.TypeConversion):
        #     pass

        elif isinstance(ir, operations.SolidityCall):
            if ir.function.name.startswith('require'):
                mstate.add_constraint(mstate.get_z3_var(ir.arguments[0]))
            else:
                assert False, '未处理的 solidity call'

        elif isinstance(ir, operations.InternalCall):
            if isinstance(ir.function, Function):
                if ir.is_modifier_call:
                    # 暂未考虑 modifier 的情况
                    return
                if ir.function.name == "_safeTransfer":
                    token_addr = mstate.get_z3_var(ir.arguments[0])
                    from_ = mstate.call_stack[-1].target
                    to = mstate.get_z3_var(ir.arguments[1])
                    amount = mstate.get_z3_var(ir.arguments[2])
                    
                    cur_amount_of_from = mstate.wstate.get_storage(token_addr, f"_balances.{from_}")
                    cur_amount_of_to = mstate.wstate.get_storage(token_addr, f"_balances.{to}")
                    mstate.wstate.set_storage(token_addr, f"_balances.{from_}", cur_amount_of_from - amount)
                    mstate.wstate.set_storage(token_addr, f"_balances.{to}", cur_amount_of_to + amount)
                    # call = copy(mstate.call_stack[-1])
                    # call.call_type = CallType.External
                    # call.target = mstate.get_z3_var(ir.arguments[0])
                    # call.function_signature = "transfer(address,uint256)"
                    # call.params = [mstate.get_z3_var(ir.arguments[1]), mstate.get_z3_var(ir.arguments[2])]
                    # call.msg_sender = mstate.call_stack[-1].target
                    # call.msg_value = 0
                    # mstate.call_stack.append(call)
                    # print("——————开始外部调用——————")
                    # self.exec_call(mstate)
                    # print("——————结束外部调用——————")
                    return
                if ir.function.name == "self_balance_of":
                    token_addr = mstate.get_z3_var(ir.arguments[0])
                    z3_var = mstate.wstate.get_storage(token_addr, f"_balances.{mstate.call_stack[-1].target}")
                    mstate.set_z3_var(ir.lvalue, z3_var)
                    return 
                if ir.function.name == "_update":
                    return
                    
                call = copy(mstate.call_stack[-1])
                call.call_type = CallType.Internal

                name, parameters, _ = ir.function.signature
                call.function_signature = name + "(" + ",".join(parameters) + ")"
                call.params = []
                for i in range(ir.nbr_arguments):
                    call.params.append(mstate.get_z3_var(ir.arguments[i]))

                mstate.call_stack.append(call)
                print("——————开始内部调用——————")
                self.exec_call(mstate)
                print("——————结束内部调用——————")

                mstate.set_z3_var(ir.lvalue, mstate.last_return)
            else:
                assert False, '未处理的 internal call'

        elif isinstance(ir, operations.LibraryCall):
            if ir.destination.name == "SafeMath":
                left_value_z3 = mstate.get_z3_var(ir.arguments[0])
                right_value_z3 = mstate.get_z3_var(ir.arguments[1])
                if ir.function_name == "mul":
                    lvalue_z3 = left_value_z3 * right_value_z3
                elif ir.function_name == "sub":
                    lvalue_z3 = left_value_z3 - right_value_z3
                else:
                    assert False, "未支持的操作"
                mstate.set_z3_var(ir.lvalue, lvalue_z3)
            else:
                assert False,"未支持的库调用"
            
        # elif isinstance(ir, operations.HighLevelCall):
            # 与InternalCall的情况其实类似

            # pass

        elif isinstance(ir, operations.Return):
            mstate.set_last_return(ir.values)
            mstate.call_stack.pop()

        elif isinstance(ir, operations.Unpack):
            last_return:Return = mstate.get_z3_var(ir.tuple)
            z3_v = mstate.get_z3_var(last_return.vals[ir.index]) 
            mstate.set_z3_var(ir.lvalue, z3_v)

        elif isinstance(ir, operations.Condition):
            # 在node层进行处理
            pass

        elif isinstance(ir, operations.EventCall):
            pass

        else:
            assert False, '未处理的ir'

    def add_if_cond_and_travel(self, mstate:MachineState, node: Node, if_true: bool, is_loop:bool=False):
        assert node.type == NodeType.IFLOOP if is_loop else NodeType.IF
        for ir in node.irs:
            if isinstance(ir, operations.Condition):
                z3_cond = mstate.get_z3_var(ir.value)
                if if_true:
                    mstate.add_constraint(z3_cond)
                else:
                    mstate.add_constraint(z3.Not(z3_cond))

                if mstate.check_constraints():
                    if is_loop and not if_true:
                        mstate.loop_pop()
                    son_node = node.son_true if if_true else node.son_false
                    self.travel(mstate, son_node)
                else:
                    self.mstate_check_constraints[mstate] = False

    def travel(self, mstate:MachineState, node:Node):
        mstate.exec_path.append(node)
        print(node)
        for ir in node.irs:
            print(f"\t{ir}")
            self.exec_ir(mstate, ir)
        
        if node.type == NodeType.IF:
            mstate_if_false = deepcopy(mstate)
            self.mstate_check_constraints[mstate_if_false] = True

            self.add_if_cond_and_travel(mstate, node, True)
            self.add_if_cond_and_travel(mstate_if_false, node, False)

        elif node.type == NodeType.IFLOOP:
            mstate.loop_push(node)

            mstate_if_false = deepcopy(mstate)
            self.mstate_check_constraints[mstate_if_false] = True

            if mstate.get_loop_reach_count(node) <= LOOP_MAX :
                self.add_if_cond_and_travel(mstate, node, True, is_loop=True)
            self.add_if_cond_and_travel(mstate_if_false, node, False, is_loop=True)

        elif node.type == NodeType.RETURN:
            # call_return操作在ir中完成
            pass

        else:
            if node.sons:
                self.travel(mstate, node.sons[0])
            else:
                mstate.call_return()

    def exec_call(self, mstate:MachineState):
        assert mstate.call_stack
        cur_function = mstate.get_cur_function()
        params = mstate.call_stack[-1].params
        if cur_function.parameters:
            assert len(params) == len(cur_function.parameters)
            for i in range(len(params)):
                mstate.set_z3_var(cur_function.parameters[i],params[i])
        self.travel(mstate, cur_function.entry_point)

    def start(self, wstate:WorldState, call: Call):
        mstate = MachineState(wstate, call_stack=[call])
        self.mstate_check_constraints[mstate] = True
        self.exec_call(mstate)

        for mstate, end_normally in self.mstate_check_constraints.items():
            if end_normally:
                reserve0 = mstate.wstate.get_storage(1, "reserve0")
                reserve1 = mstate.wstate.get_storage(1, "reserve1")
                balance_of_token0 =  mstate.wstate.get_storage(2, "_balances.1")
                balance_of_token1 =  mstate.wstate.get_storage(3, "_balances.1")
                mstate.add_constraint(balance_of_token0*balance_of_token1 < reserve0*reserve1)
                result = mstate.check_constraints()
                if result:
                    print("该基于uniswap v2的合约的swap方法存在K值交易后变小的情况")
                    break
        