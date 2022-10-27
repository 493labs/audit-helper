from typing import List
from ...base_node import TokenDecisionNode, NodeReturn
from ...token import ERC20_E_view, ERC721_E_view, TokenInfo

from slither.core.declarations import Function, SolidityFunction
from slither.slithir.operations import Binary, BinaryType
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.cfg.node import Node, NodeType


def node_has_risk(node: Node):
    for ir in node.irs:
        if isinstance(ir, Binary) and ir.type in [
            BinaryType.ADDITION,
            BinaryType.SUBTRACTION,
            BinaryType.MULTIPLICATION,
            BinaryType.POWER
        ]:
            # 依赖输入参数，并且回溯之前的节点，没有在if中
            for p in node.function.parameters:
                for v in ir.get_variable:
                    dependent_on_p = False
                    read_in_if = False
                    # if is_dependent(v, p, node.function):
                    if v == p:
                        dependent_on_p = True
                        cur_n = node
                        while True:
                            if len(cur_n.fathers) == 0:
                                break
                            father_n = cur_n.fathers[0]
                            if v in father_n.variables_read and (father_n.type == NodeType.IF or father_n.contains_require_or_assert()):
                                read_in_if = True
                                break
                            cur_n = father_n
                    if dependent_on_p and not read_in_if:
                        return True
    return False


def overflow_check(f: Function) -> List[Node]:
    if f.compilation_unit.solc_version >= "0.8.0":
        return None
    nodes_have_risk = []
    for node in f.nodes:
        if node_has_risk(node):
            nodes_have_risk.append(node)

    for internal_call in f.internal_calls:
        if not isinstance(internal_call, SolidityFunction):
            internal_ret = overflow_check(internal_call)
            if internal_ret:
                nodes_have_risk.extend(internal_ret)
    return nodes_have_risk


class OverflowNode(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        if token_info.is_erc20:
            nodes_have_risk: List[Node] = []
            for e in [ERC20_E_view.balanceOf, ERC20_E_view.allowance]:
                for f in token_info.enum_to_state_to_funcs(e):
                    nodes = overflow_check(f)
                    if nodes:
                        nodes_have_risk.extend(nodes)
            if len(nodes_have_risk) == 0:
                self.add_info('溢出检查未发现异常')
            else:
                for node in set(nodes_have_risk):
                    self.add_warns(f'{node.function.canonical_name}:{node.expression}具有溢出风险')
        return NodeReturn.branch0
