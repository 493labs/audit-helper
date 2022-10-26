from enum import Enum, unique
from re import T
from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.common.e import Chain
from core.utils.scan_api import get_sli_c_by_addr
from .common.token import TokenInfo
from .common.base_node import generate_node, NodeReturn

from .nodes.token_type import TokenTypeNode
from .nodes.state import StateNode
from .nodes.write_close import CloseCheckNode
from .nodes.func_read_write import RequiredFuncNode

from .nodes.transfer.search_loop import SearchLoop
from .nodes.transfer.transfer_other import TransferOtherNode

from .nodes.mint.cheat_state import CheatState
from .nodes.mint.arbitrary_mint import ArbitraryMint

from .nodes.general.back_door import BackDoorNode
from .nodes.general.external_call import ExternalCallNode
from .nodes.general.calculation_order import CalculationOrder
from .nodes.general.not_zero_address import NotZeroAddress

from .nodes.erc20.overflow import OverflowNode
from .nodes.erc20.fake_recharge import FakeRecharge


decision_tree = {
    TokenTypeNode: [StateNode, TokenTypeNode],
    StateNode: [CloseCheckNode],
    CloseCheckNode: [RequiredFuncNode],
    RequiredFuncNode: [SearchLoop],

    # transfer 相关
    SearchLoop: [TransferOtherNode],
    TransferOtherNode: [CheatState],

    # mint 相关
    CheatState: [ArbitraryMint],
    ArbitraryMint: [CalculationOrder],

    # 通用性
    CalculationOrder: [ExternalCallNode],
    ExternalCallNode: [BackDoorNode],
    BackDoorNode: [NotZeroAddress],
    NotZeroAddress: [OverflowNode],

    # erc20 特有
    OverflowNode: [FakeRecharge]
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