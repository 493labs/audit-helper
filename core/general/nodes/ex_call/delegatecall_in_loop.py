from typing import List, Optional, Tuple, Set
from slither.core.declarations import Contract, Function, FunctionContract
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations import LowLevelCall, InternalCall
from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

# 循环中有委托调用
class DelegatecallInLoopNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        nodes = detect_delegatecall_in_loop(contract_info.c)
        fnames = set([node.function.name for node in nodes])
        if len(fnames) > 0:
            fnamesStr = ','.join(fnames)
            self.add_warn(f'{fnamesStr} 在循环中存在委托调用')
        return NodeReturn.branch0

def detect_delegatecall_in_loop(contract: Contract) -> List[Node]:
    results: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented and f.payable:
            delegatecall_in_loop(f.entry_point, 0, [], results)
    return results

def delegatecall_in_loop(
    node: Optional[Node], in_loop_counter: int, visited: List[Node], results: List[Node]
) -> None:

    if node is None:
        return

    if node in visited:
        return
    # shared visited
    visited.append(node)

    if node.type == NodeType.STARTLOOP:
        in_loop_counter += 1
    elif node.type == NodeType.ENDLOOP:
        in_loop_counter -= 1

    for ir in node.all_slithir_operations():
        if (
            in_loop_counter > 0
            and isinstance(ir, (LowLevelCall))
            and ir.function_name == "delegatecall"
        ):
            results.append(ir.node)
        if isinstance(ir, (InternalCall)) and ir.function:
            delegatecall_in_loop(ir.function.entry_point, in_loop_counter, visited, results)

    for son in node.sons:
        delegatecall_in_loop(son, in_loop_counter, visited, results)
