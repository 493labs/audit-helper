from enum import Enum, unique
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.common.e import Chain
from .common.token import TokenInfo
from .common.base_node import generate_node, NodeReturn, DecisionScheme

from .nodes.token_type import TokenTypeNode
from .nodes.state import Erc20StateNode, Erc721StateNode
from .nodes.write_close import Erc20CloseCheckNode, Erc721CloseCheckNode
from .nodes.overflow import OverflowNode
from .nodes.func_read_write import Erc20RequiredFuncNode, Erc721RequiredFuncNode


decision_tree = {
    TokenTypeNode: [Erc20StateNode, Erc721StateNode, TokenTypeNode],
    Erc20StateNode: [OverflowNode],
    OverflowNode: [Erc20CloseCheckNode],
    Erc20CloseCheckNode: [Erc20RequiredFuncNode],
    Erc721StateNode: [Erc721CloseCheckNode],
    Erc721CloseCheckNode: [Erc721RequiredFuncNode]
}

def make_decision(mode: DecisionScheme, c: Contract, chain: Chain=None, address: ChecksumAddress = None ):
    token_info = TokenInfo()
    token_info.c = c
    token_info.chain = chain
    token_info.address = address

    cur_node = generate_node(TokenTypeNode, None, mode)
    while True:
        ret = cur_node.check(token_info)
        if ret == NodeReturn.reach_leaf:
            return cur_node.output()
        next_node = decision_tree[cur_node.__class__][ret.value]
        cur_node = generate_node(next_node, cur_node, mode)
