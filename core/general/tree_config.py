from .nodes.dangerous_opcode import DangerousOpcodeNode
from .nodes.authentication import AuthenticationNode
from .nodes.external_call import DangerousExCallNode

decision_tree = {
    AuthenticationNode: DangerousExCallNode,
    DangerousExCallNode:DangerousOpcodeNode
}