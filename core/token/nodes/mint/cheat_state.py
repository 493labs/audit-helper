from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_view, TokenInfo
from slither.core.solidity_types import ElementaryType

class CheatState(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        cap_states = [s for s in token_info.c.state_variables \
            if isinstance(s.type, ElementaryType) \
                and 'uint' in s.type.type \
                    and s.name in ['maxSupply','cap']
        ]
        if cap_states:
            mint_fs = token_info.get_mint_fs()
            for mint_f in mint_fs:
                params = [param for param in mint_f.parameters \
                    if isinstance(param.type, ElementaryType) \
                        and 'uint' in param.type.type\
                            and not mint_f.is_reading_in_require_or_assert(param)
                ]
                if params:
                    cap_names = ','.join([cap_s.name for cap_s in cap_states])
                    param_names = ','.join([param.name for param in params])
                    self.add_warn(f'{token_info.c.name} 合约中存在最大上限相关定义 {cap_names} ，但其mint方法 {mint_f.name} 中的参数 {param_names} 未进行校验')

        if token_info.is_erc20:
            totalSupply_state = token_info.state_map[ERC20_E_view.totalSupply]
            mint_fs = token_info.get_mint_fs()
            cheat_fs = [f for f in mint_fs if totalSupply_state not in f.all_state_variables_written()]

            if len(cheat_fs) == 0:
                self.add_info(f'未发现 {totalSupply_state.name} 未增加的 mint 行为')
            else:
                fnames = ','.join([f.full_name for f in cheat_fs])
                self.add_warn(f'{fnames} 存在 mint 行为但 {totalSupply_state.name} 未增加')  

        return NodeReturn.branch0