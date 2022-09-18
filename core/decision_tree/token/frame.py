from slither.core.declarations import Contract
from .common.standard import TokenInfo
from .common.base_node import generate_node, NodeReturn

from .nodes.token_type import TokenTypeNode
from .nodes.state import Erc20StateNode
from .nodes.write_close import CloseCheckNode
from .nodes.overflow import OverflowNode
from .nodes.func_read_write import RequiredFuncNode


decision_tree = {
    TokenTypeNode: [Erc20StateNode],
    Erc20StateNode: [OverflowNode],
    OverflowNode: [CloseCheckNode],
    CloseCheckNode: [RequiredFuncNode]
}

def run(c: Contract):
    token_info = TokenInfo()
    token_info.c = c
    cur_node = generate_node(TokenTypeNode, None)
    while True:
        ret = cur_node.check(token_info)
        if ret == NodeReturn.reach_leaf:
            return cur_node.output()
        next_node = decision_tree[cur_node.__class__][ret.value]
        cur_node = generate_node(next_node, cur_node)
