from enum import Enum, unique
from re import T
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.common.e import Chain
from core.utils.source_code import get_sli_c_by_addr
from .common.token import TokenInfo
from .common.base_node import generate_node, NodeReturn

from .nodes.token_type import TokenTypeNode
from .nodes.state import Erc20StateNode, Erc721StateNode
from .nodes.write_close import CloseCheckNode
from .nodes.overflow import OverflowNode
from .nodes.func_read_write import RequiredFuncNode
from .nodes.transfer_other import TransferOtherNode
from .nodes.external_call import ExternalCallNode
from .nodes.back_door import BackDoorNode


decision_tree = {
    TokenTypeNode: [Erc20StateNode, Erc721StateNode, TokenTypeNode],
    Erc20StateNode: [OverflowNode],
    OverflowNode: [TransferOtherNode],
    TransferOtherNode: [CloseCheckNode],    
    Erc721StateNode: [CloseCheckNode],
    CloseCheckNode: [RequiredFuncNode],
    RequiredFuncNode: [ExternalCallNode],
    ExternalCallNode: [BackDoorNode]
}

def make_decision(on_chain: bool=False, chain: Chain=None, address: ChecksumAddress = None, c: Contract=None ):
    token_info = TokenInfo()
    token_info.chain = chain
    token_info.address = address
    if c == None:
        c = get_sli_c_by_addr(chain, address)
    token_info.c = c
    token_info.state_map = {}
    token_info.func_map = {}
    token_info.state_to_funcs_map = {}

    cur_node = generate_node(TokenTypeNode, None, on_chain)
    while True:
        ret = cur_node.check(token_info)
        if ret == NodeReturn.reach_leaf:
            break                    
        if cur_node.__class__ not in decision_tree:
            break
        next_node = decision_tree[cur_node.__class__][ret.value]
        cur_node = generate_node(next_node, cur_node, on_chain)

    return cur_node.output()