from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import ERC20_E_Require, TokenInfo, ERC20_E_view, ERC721_E_view

from typing import Tuple
from slither.core.declarations import SolidityFunction
from slither.core.variables.state_variable import StateVariable
from slither.core.cfg.node import Node, NodeType
def get_dominance_frontier(node: Node)-> Node:
    if node.type == NodeType.IFLOOP:
        # 循环时的边界指向了循环
        return node.son_false.sons[0]
    elif node.type == NodeType.IF:
        return list(node.dominance_frontier)[0]

def if_dominance_read_state(if_node:Node, state:StateVariable)-> bool:
    assert if_node.type == NodeType.IF, f'if_dominance_read_state 的参数需要为if节点：{if_node.expression}'
    if if_node.son_true:
        is_read, contain_return = branch_read_state(if_node.son_true, state)
        if not is_read :
            return False, contain_return
    if if_node.son_false:
        is_read, contain_return = branch_read_state(if_node.son_false, state)
        if not is_read :
            return False, contain_return
    return True, contain_return

def branch_read_state(node:Node, state:StateVariable)->Tuple[bool,bool]:
    is_read = False
    contain_return = False
    while True:
        if state in node.state_variables_read:
            is_read = True
            break
        for internal_call in node.internal_calls:
            if not isinstance(internal_call, SolidityFunction):
                if branch_read_state(internal_call.entry_point,state)[0]:
                    is_read = True
                    break

        if node.type == NodeType.RETURN:
            contain_return = True
            break

        if node.type == NodeType.IF:
            is_read, contain_return = if_dominance_read_state(node, state)
            if not is_read and contain_return:
                break
            else:
                node = get_dominance_frontier(node)
                continue 

        if node.type == NodeType.IFLOOP:  
            # 暂不考虑循环的细节处理 
            node = get_dominance_frontier(node)
            continue      

        
        if len(node.sons) == 0:
            break
        if node.immediate_dominator in node.sons:
            break        
        # assert len(node.sons) == 1, f'len(node.sons) != 1'
        node = node.sons[0]
    return (is_read, contain_return)


class TransferOtherNode(DecisionNode):
    
    def check(self, token_info: TokenInfo) -> NodeReturn:
        transfer_other_func = token_info.get_f(ERC20_E_Require.transferFrom)
        allow_state = token_info.state_map[ERC20_E_view.allowance]
        if branch_read_state(transfer_other_func.entry_point, allow_state)[0]:
            self.add_info(f'未发现 {transfer_other_func.name} 有转移其他人代币的实现')
        else:
            self.add_warn(f'{transfer_other_func.name} 存在未读取 {allow_state.name} 的路径')
        return NodeReturn.branch0

