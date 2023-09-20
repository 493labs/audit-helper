from .nodes.authentication.unauthorized_write import UnauthorizedWriteNode
from .nodes.ex_call.excall_depend_on_tx_input import ExCallDependOnTxInputNode
from .nodes.ex_call.reentrant import ReentrantNode
from .nodes.ex_call.delegatecall_in_loop import DelegatecallInLoopNode
from .nodes.ex_call.unchecked_low_level_call import UncheckedLowLevelCallNode
from .nodes.others.dangerous_opcode import DangerousOpcodeNode
from .nodes.others.weak_prng import WeakPrng

decision_tree = {
    UnauthorizedWriteNode: [ExCallDependOnTxInputNode],
    ExCallDependOnTxInputNode: [ReentrantNode],
    ReentrantNode: [DelegatecallInLoopNode],
    DelegatecallInLoopNode: [UncheckedLowLevelCallNode],
    UncheckedLowLevelCallNode: [DangerousOpcodeNode],
    DangerousOpcodeNode: [WeakPrng]
}
