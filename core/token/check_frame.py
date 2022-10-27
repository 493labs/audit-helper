from typing import List, Mapping
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.utils.url import Chain
from core.utils.scan_api import get_sli_c_by_addr
from core.frame.frame import make_decision

from .token import TokenInfo
from .base_node import TokenDecisionNode
from .tree_config import token_decision_tree, TokenTypeNode

def token_decision(        
        on_chain: bool=False, 
        chain: Chain=None, 
        address: ChecksumAddress = None, 
        c: Contract=None,
        decision_tree: Mapping[TokenDecisionNode, List[TokenDecisionNode]] = token_decision_tree,
        start_node: type[TokenDecisionNode] = TokenTypeNode  
    ):
    token_info = TokenInfo()
    token_info.chain = chain
    token_info.address = address
    if c == None:
        c = get_sli_c_by_addr(chain, address)
    token_info.c = c
    token_info.state_map = {}
    token_info.func_map = {}
    token_info.state_to_funcs_map = {}

    return make_decision(decision_tree, start_node, token_info, on_chain)
