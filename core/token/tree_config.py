from .nodes.token_type import TokenTypeNode
from .nodes.state import StateNode
from .nodes.write_close import CloseCheckNode
from .nodes.func_read_write import RequiredFuncNode

from .nodes.transfer.search_if_and_loop import SearchIfAndLoop
from .nodes.transfer.transfer_other import TransferOtherNode

from .nodes.mint.cheat_state import CheatState
from .nodes.mint.arbitrary_mint import ArbitraryMint

from .nodes.general.back_door import BackDoorNode
from .nodes.general.external_call import ExternalCallNode
from .nodes.general.calculation_order import CalculationOrder
from .nodes.general.not_zero_address import NotZeroAddress
from .nodes.general.meta_transaction import MetaTransaction

from .nodes.erc20.overflow import OverflowNode
from .nodes.erc20.fake_recharge import FakeRecharge

token_decision_tree = {
    TokenTypeNode: [StateNode, TokenTypeNode],
    StateNode: [CloseCheckNode],
    CloseCheckNode: [RequiredFuncNode],
    RequiredFuncNode: [SearchIfAndLoop],

    # transfer 相关
    SearchIfAndLoop: [TransferOtherNode],
    TransferOtherNode: [CheatState],

    # mint 相关
    CheatState: [ArbitraryMint],
    ArbitraryMint: [CalculationOrder],

    # 通用性
    CalculationOrder: [ExternalCallNode],
    ExternalCallNode: [BackDoorNode],
    BackDoorNode: [NotZeroAddress],
    NotZeroAddress: [MetaTransaction],
    MetaTransaction: [OverflowNode],

    # erc20 特有
    OverflowNode: [FakeRecharge]
}
