from enum import Enum
from typing import List, Tuple, Union
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable

from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import ERC20_E_view, ERC721_E_view, TokenInfo

def get_e_view_state(c:Contract, e_view:Union[ERC20_E_view, ERC721_E_view] )->List[StateVariable]:
    for s in c.state_variables:
        if s.name == e_view.name:
            return [s]
    f = c.get_function_from_signature(e_view.value)
    if f:
        return [s for s in f.all_state_variables_read() if not (s.is_constant or s.is_immutable)]
    return None

class StateNode(DecisionNode):
    
    def check(self, token_info: TokenInfo) -> NodeReturn:        
        if token_info.is_erc20:
            token_e_view = ERC20_E_view
        elif token_info.is_erc721:
            token_e_view = ERC721_E_view

        warns = []
        for e in token_e_view._member_map_.values():
            states = get_e_view_state(token_info.c,e)
            if states == None:
                warns.append(f'{e.name} 未找到相应的状态变量')
                continue

            if token_info.is_erc721a and e in [ERC721_E_view.ownerOf, ERC721_E_view.getApproved]:
                # erc721a 的实现中可能会读取_currentIndex，影响后面的分析
                states = [s for s in states if s.name != '_currentIndex']
            if e == ERC721_E_view.getApproved:
                # 有些erc721实现会先通过ownerOf判断tokenId是否存在，再进一步读取approve
                owner_state = token_info.state_map[ERC721_E_view.ownerOf]
                states = [s for s in states if s != owner_state]

            states_count = len(states)            
            if states_count != 1:
                state_names = ','.join([state.name for state in states])
                warns.append(f'{e.name} 读取的状态变量有 {state_names}')
                continue

            token_info.state_map[e] = states[0]
        
        if len(warns) > 0:
            self.add_warns(warns)
            return NodeReturn.reach_leaf
        else:
            e_view_names = ','.join(token_e_view._member_names_)
            self.add_info(f'关于 {e_view_names} 的状态定义没有异常')
            return NodeReturn.branch0

