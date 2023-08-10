from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC721_E_view, TokenInfo

from slither.core.solidity_types import ElementaryType, UserDefinedType, MappingType
from slither.core.declarations import Function, SolidityFunction, Contract

class ArbitraryMint(TokenDecisionNode):

    def read_address(self, mint_f:Function, token_info:TokenInfo) -> bool:
        for node in mint_f.all_nodes():
            if node.is_conditional(): 
                states_read_in_internal_call = [state for call in node.internal_calls if not isinstance(call, SolidityFunction) for state in call.all_state_variables_read() ]                   
                for state in node.state_variables_read + states_read_in_internal_call:
                    # 考虑下面的定义，实质上是一个地址
                    # ECOx
                    # Policy public immutable policy;
                    if isinstance(state.type, UserDefinedType) and isinstance(state.type.type, Contract):
                        return True
                    # 还需要考虑mapping的情况，所以不适用 if state.type == ElementaryType("address"):
                    if "address" in str(state.type):
                        if token_info.is_erc721 and state == token_info.state_map[ERC721_E_view.ownerOf]:
                            # 考虑某些erc721实现中，在操作token时先通过ownerOf先判断该ID是否存在
                            continue
                        return True
                    # 'AccessControl.RoleData' 情况
                    if isinstance(state.type, MappingType) and isinstance(state.type.type_to, UserDefinedType) and 'RoleData' in state.type.type_to.type.name:
                        return True
        return False
        
        
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        mint_fs = token_info.get_mint_fs()
        dangerous_fs = [f for f in mint_fs if not self.read_address(f, token_info)]
        
        if len(dangerous_fs) == 0:
            self.add_info(f'未发现不经授权就可任意 mint 的方法')
        else:
            fnames = ','.join([f.name for f in dangerous_fs])
            self.add_warn(f'{fnames} 存在不经授权就可任意 mint 的风险')  
        return NodeReturn.branch0