from typing import List, Optional, Tuple, Set
from slither.core.declarations import Contract, Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import LowLevelCall, InternalCall
from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

# 未检查低级别调用的返回值
class UncheckedLowLevelCallNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        nodes:List[Node] = []
        for f in contract_info.c.functions_and_modifiers:
            nodes.extend(detect_unused_return_values(f))
        for node in nodes:
            self.add_warn(f'{node.function.name} 的 {node.expression} 存在未检查的低级别调用')
        return NodeReturn.branch0

def detect_unused_return_values(f: FunctionContract) -> List[Node]:
    values_returned = []
    nodes_origin = {}
    for n in f.nodes:
        for ir in n.irs:
            if isinstance(ir, LowLevelCall):
                # if a return value is stored in a state variable, it's ok
                if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                    values_returned.append(ir.lvalue)
                    nodes_origin[ir.lvalue] = ir

            for read in ir.read:
                if read in values_returned:
                    values_returned.remove(read)

    return [nodes_origin[value].node for value in values_returned]
