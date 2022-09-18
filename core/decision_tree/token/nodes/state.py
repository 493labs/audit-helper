from typing import List, Union
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable

from ..common.base_node import DecisionNode, NodeReturn
from ..common.standard import ERC20_E_view, ERC721_E_view, TokenInfo

def get_e_view_state(c:Contract, e_view:Union[ERC20_E_view, ERC721_E_view] )->List[StateVariable]:
    for s in c.state_variables:
        if s.name == e_view.name:
            return [s]
    f = c.get_function_from_signature(e_view.value)
    if f:
        return f.state_variables_read
    return None


class Erc20StateNode(DecisionNode):

    def check(self, token_info:TokenInfo) -> NodeReturn:        
        for e in ERC20_E_view._member_map_.values():
            states = get_e_view_state(token_info.c,e)
            if states == None:
                self.layerouts.append(f'{e.name}未找到相应的状态变量')
                return NodeReturn.reach_leaf
            states_count = len(states)
            if states_count != 1:
                self.layerouts.append(f'{e.name}读取的状态变量有{states_count}个')
                return NodeReturn.reach_leaf
            token_info.state_map[e] = states[0]
        self.layerouts.append('关于totalsupply、balances、allowance的状态定义没有异常')
        return NodeReturn.branch0

class Erc721Node(DecisionNode):
    pass
