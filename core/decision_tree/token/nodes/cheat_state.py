from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import ERC20_E_view, TokenInfo, ERC20_E_Require, ERC20_E_Extend, ERC721_E_Require, ERC721_E_view

from slither.slithir.operations import LibraryCall, Binary, BinaryType

class CheatState(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
        if token_info.is_erc20:
            balance_state = token_info.state_map[ERC20_E_view.balanceOf]
            totalSupply_state = token_info.state_map[ERC20_E_view.totalSupply]

            cheat_fs = []
            for f in token_info.c.functions_entry_points:
                if f.is_constructor:
                    continue
                if balance_state not in f.all_state_variables_written():
                    continue
                if totalSupply_state in f.all_state_variables_written():
                    continue

                have_sub_op = False
                for node in f.all_nodes():
                    if balance_state in node.state_variables_written:
                        for ir in node.irs:
                            if isinstance(ir, LibraryCall) and ir.function_name == 'sub':
                                have_sub_op = True
                                break
                            if isinstance(ir, Binary) and ir.type == BinaryType.SUBTRACTION:
                                have_sub_op = True
                                break
                    if have_sub_op:
                        break
                if not have_sub_op:
                    cheat_fs.append(f)

            if len(cheat_fs) == 0:
                self.add_info(f'未发现 {totalSupply_state.name} 未增加的 mint 行为')
            else:
                fnames = ','.join([f.name for f in cheat_fs])
                self.add_warn(f'{fnames} 存在 mint 行为但 {totalSupply_state.name} 未增加')  

        return NodeReturn.branch0