from enum import Enum, unique
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.common.e import Chain
from core.utils.source_code import get_sli_c_by_addr
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

def make_decision(mode: DecisionScheme=DecisionScheme.off_chain, chain: Chain=None, address: ChecksumAddress = None, c: Contract=None ):
    token_info = TokenInfo()
    token_info.chain = chain
    token_info.address = address
    if c == None:
        c = get_sli_c_by_addr(chain, address)
    token_info.c = c
    token_info.state_map = {}
    token_info.func_map = {}
    token_info.state_to_funcs_map = {}

    cur_node = generate_node(TokenTypeNode, None, mode)
    while True:
        ret = cur_node.check(token_info)
        if ret == NodeReturn.reach_leaf:
            return cur_node.output()
        next_node = decision_tree[cur_node.__class__][ret.value]
        cur_node = generate_node(next_node, cur_node, mode)
