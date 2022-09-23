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
        return f.state_variables_read
    return None

def _check(token_info:TokenInfo, token_e_view:type[Enum]) -> Tuple[List[str], NodeReturn]:
    for e in token_e_view._member_map_.values():
        states = get_e_view_state(token_info.c,e)
        if states == None:
            return [f'{e.name}未找到相应的状态变量'], NodeReturn.reach_leaf
        states_count = len(states)
        if states_count != 1:
            return [f'{e.name}读取的状态变量有{states_count}个'], NodeReturn.reach_leaf
        token_info.state_map[e] = states[0]
    state_names = ','.join([token_info.state_map[state_e].name for state_e in token_e_view._member_map_.values()])
    return [f'关于 {state_names} 的状态定义没有异常'], NodeReturn.branch0

class Erc20StateNode(DecisionNode):

    def check(self, token_info:TokenInfo) -> NodeReturn:    
        layerouts, node_return = _check(token_info, ERC20_E_view)
        self.layerouts.extend(layerouts)
        return node_return   

class Erc721StateNode(DecisionNode):
    
    def check(self, token_info:TokenInfo) -> NodeReturn:    
        layerouts, node_return = _check(token_info, ERC721_E_view)
        if node_return == NodeReturn.branch0:
            self.add_infos(layerouts)
        elif node_return == NodeReturn.reach_leaf:
            self.add_warns(layerouts)
        return node_return
