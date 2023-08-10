from typing import List
from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC721_E_Extend, TokenInfo

from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable


class BaseURICheck(TokenDecisionNode):
    
    def get_baseuri_state(self, c:Contract)-> List[StateVariable]:
        f = c.get_function_from_signature(ERC721_E_Extend.baseuri.value)
        if f:
            return [s for s in f.all_state_variables_read() if not (s.is_constant or s.is_immutable)]
        #return None

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        warns = []
        if token_info.is_erc721:            
            baseuri_state = self.get_baseuri_state(token_info.c)
            if baseuri_state:
                if len(baseuri_state) == 1:
                    write_baseuri_funcs = token_info.state_to_funcs(baseuri_state[0])
                    if write_baseuri_funcs:
                        for f in write_baseuri_funcs:
                            warns.append(f'{f.name} 方法对 {baseuri_state[0]} 具有有写入操作') 
        
        if len(warns) == 0:
            self.add_info(f'关于 baseURI 的状态定义没有异常')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0