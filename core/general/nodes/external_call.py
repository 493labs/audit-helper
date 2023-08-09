from typing import List, Mapping
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import Contract, Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.core.cfg.node import Node
from slither.core.expressions import MemberAccess, Identifier, TypeConversion
from slither.slithir.operations import HighLevelCall, LowLevelCall, LibraryCall
from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

class DangerousExCallNode(DecisionNode):
    
    def check(self, contract_info: ContractInfo) -> NodeReturn:
        writable_entry = list(filter(lambda f:not f.view and not f.pure, contract_info.c.functions_entry_points))
        for f in writable_entry:
            for ex_call_expression in f.external_calls_as_expressions:
                called: MemberAccess = ex_call_expression.called
                ex: Identifier
                if isinstance(called.expression, TypeConversion):
                    ex = called.expression.expression
                else:
                    ex = called.expression
                for entry in writable_entry:
                    for param in entry.parameters:
                        if is_dependent(ex.value, param, contract_info.c):
                            self.add_warn("危险的外部调用：{} 中的 {} 依赖于 {} 的参数 {}".format(
                                f.name, ex_call_expression, entry.name, param.name
                            ))
        return NodeReturn.branch0

# class ReentrantNode(DecisionNode):

#     def check(self, contract_info: ContractInfo) -> NodeReturn:
#         for f in contract_info.c.functions_entry_points:
#             if f.is_constructor:
#                 continue

#             all_slithir_operations = f.all_slithir_operations() 

#             has_external_call = False
#             for i in range(len(all_slithir_operations)):
#                 ir = all_slithir_operations[i]        
#                 if (isinstance(ir, HighLevelCall) and not isinstance(ir, LibraryCall)) or isinstance(ir, LowLevelCall):  
#                     has_external_call = True
#                     break

#             if has_external_call:
#                 state_variables_written:List[StateVariable] = []
#                 node_parsed:Mapping[Node,bool] = {}
#                 for j in range(i, len(all_slithir_operations)):
#                     ir = all_slithir_operations[j]
#                     if ir.node not in node_parsed:
#                         node_parsed[ir.node] = True
#                         if len(ir.node.state_variables_written) > 0:
#                             state_variables_written.extend(ir.node.state_variables_written)
#                             state_variables_written = list(set(state_variables_written))  
                            

#                 if len(state_variables_written) > 0:
#                     if not self._has_nonReentrant_mechanism(f):
#                         self.add_warn(f'{f.name} 的 {all_slithir_operations[i].node.expression} 存在针对自身的重入风险')
#                     f:FunctionContract = f
#                     for ff in f.contract.functions_entry_points:
#                         if ff == f or ff.is_constructor or ff.view or ff.pure:
#                             continue
#                         read_the_writed_state = False
#                         for s in ff.all_state_variables_read():
#                             if s in state_variables_written:
#                                 read_the_writed_state = True
#                                 break
#                         if read_the_writed_state and not self._has_nonReentrant_mechanism(ff):
#                             self.add_warn(f'{f.name} 的 {all_slithir_operations[i].node.expression} 存在针对 {ff.name} 的重入风险')
        
#     def _has_nonReentrant_mechanism(self, f:Function) -> bool:
#         '''
#         是否具有防重入机制
#         '''
#         for m in f.modifiers:
#             if m.name == 'nonReentrant':
#                 return True
#         return False

# 循环中有委托调用
