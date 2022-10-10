from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import ERC20_E_view, TokenInfo

class CheatState(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
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