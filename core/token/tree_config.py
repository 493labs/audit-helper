from .nodes.token_type import TokenTypeNode
from .nodes.state import StateNode
from .nodes.write_close import CloseCheckNode
from .nodes.func_read_write import RequiredFuncNode

from .nodes.transfer.search_if_and_loop import SearchIfAndLoop
from .nodes.transfer.transfer_other import TransferOtherNode
from .nodes.transfer.transfer_fee import TransferFeeCheck
from .nodes.transfer.black_white_list import BlackWhiteListCheck
from .nodes.transfer.transfer_safeguard import TransferSafeGuardCheck
from .nodes.transfer.transfer_restriction import TransferRestrictionCheck

from .nodes.mint.cheat_state import CheatState
from .nodes.mint.arbitrary_mint import ArbitraryMint
from .nodes.mint.unlimit_mint import UnlimitMint

from .nodes.general.back_door import BackDoorNode
from .nodes.general.external_call import ExternalCallNode
from .nodes.general.calculation_order import CalculationOrder
from .nodes.general.not_zero_address import NotZeroAddress
from .nodes.general.meta_transaction import MetaTransaction
from .nodes.general.event import EventNode
from .nodes.general.replay_attack import ReplayAttack
from .nodes.general.pausable_check import PausableCheck

from .nodes.erc20.overflow import OverflowNode
from .nodes.erc20.fake_recharge import FakeRecharge
from .nodes.erc20.balance_check import BalanceCheck

from .nodes.erc721.base_uri import BaseURICheck
from .nodes.erc721.random_check import RandomCheck

token_decision_tree = {
    TokenTypeNode: [StateNode, TokenTypeNode],
    StateNode: [CloseCheckNode],
    CloseCheckNode: [RequiredFuncNode],
    RequiredFuncNode: [SearchIfAndLoop],

    # transfer 相关
    SearchIfAndLoop: [TransferOtherNode],
    TransferOtherNode: [TransferFeeCheck],
    TransferFeeCheck: [BlackWhiteListCheck],
    BlackWhiteListCheck: [TransferSafeGuardCheck],
    TransferSafeGuardCheck: [TransferRestrictionCheck],
    TransferRestrictionCheck: [CheatState],

    # mint 相关
    CheatState: [ArbitraryMint],
    ArbitraryMint: [UnlimitMint],
    UnlimitMint: [CalculationOrder],

    # 通用性
    CalculationOrder: [ExternalCallNode],
    ExternalCallNode: [BackDoorNode],
    BackDoorNode: [NotZeroAddress],
    NotZeroAddress: [MetaTransaction],
    MetaTransaction: [ReplayAttack],
    ReplayAttack: [EventNode],
    EventNode: [PausableCheck],
    PausableCheck: [OverflowNode],

    # erc20 特有
    OverflowNode: [FakeRecharge],
    FakeRecharge: [BalanceCheck],
    BalanceCheck: [BaseURICheck],
    
    # erc721 特有
    BaseURICheck: [RandomCheck]
}
