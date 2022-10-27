from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, ERC721_E_Require, TokenInfo, ERC20_E_view, ERC721_E_view

from typing import List, Tuple
from slither.core.declarations import SolidityFunction, Function
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
                    # break 
                    # 有两层循环，不能用break
                    return is_read, contain_return

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

# 基于dominators简单实现
# 有bug，未覆盖前置程序中存在if的情况
def all_branchs_read_state(f: Function, s:StateVariable):
    for node in f.nodes_ordered_dominators:
        if node.type == NodeType.RETURN:
            all_state_read = {s for n in node.dominators for s in n.state_variables_read}
            all_internal_calls = {ic for n in node.dominators for ic in n.internal_calls}
            all_state_read |= {s for ic in all_internal_calls for s in ic.all_state_variables_read()}
            if s not in all_state_read:
                return False
    return True
    
class TransferOtherNode(TokenDecisionNode):
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        if token_info.is_erc20:
            func_es = [ERC20_E_Require.transferFrom]
            state_e = ERC20_E_view.allowance
        elif token_info.is_erc721:
            func_es = [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]
            state_e = ERC721_E_view.getApproved

        warns = []
        for func_e in func_es:
            transfer_other_func = token_info.get_f(func_e)
            allow_state = token_info.state_map[state_e]
            if not branch_read_state(transfer_other_func.entry_point, allow_state)[0]:
            # if not all_branchs_read_state(transfer_other_func, allow_state):
                warns.append(f'{transfer_other_func.full_name} 存在未读取 {allow_state.name} 的路径')

        if len(warns) == 0:
            self.add_info(f'未发现 transferFrom 模式的方法中有未经授权转移其他人代币的实现')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0

