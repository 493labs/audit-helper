from typing import List
from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_view, ERC721_E_view, TokenInfo

from slither.core.declarations import Function
from slither.slithir.operations import Binary, BinaryType, LibraryCall

class CalculationOrder(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        def search(f: Function)->List[str]:
            warns = []
            for node in f.all_nodes():
                if node.function != f:
                    # 排除进入LibraryCall内部的情况
                    continue
                mul_indexs = []
                div_indexs = []
                for i,ir in enumerate(node.irs):
                    if (isinstance(ir, Binary) and ir.type == BinaryType.MULTIPLICATION) \
                      or (isinstance(ir, LibraryCall) and ir.function_name == 'mul'):
                        mul_indexs.append(i)
                    if (isinstance(ir, Binary) and ir.type == BinaryType.DIVISION) \
                      or (isinstance(ir, LibraryCall) and ir.function_name == 'div'):
                        div_indexs.append(i)

                if len(div_indexs) > 0:
                    if len(mul_indexs) > 0 and mul_indexs[-1] > div_indexs[0]:
                        warns.append(f'{f.name} : {node.expression} 中存在先除后乘，计算出错的风险')
                    else:
                        warns.append(f'{f.name} : {node.expression} 中存在除法计算，具有损失精度的风险')
            return warns

        warns = []
        if token_info.is_erc20:
            for f in token_info.enum_to_state_to_funcs(ERC20_E_view.balanceOf):
                warns.extend(search(f))
        if token_info.is_erc721:
            for f in token_info.enum_to_state_to_funcs(ERC721_E_view.balanceOf):
                warns.extend(search(f))

        if len(warns) == 0:
            self.add_info(f'对 balanceOf 的写入方法中，未发现同时乘除的表达式')  
        else:
            self.add_warns(warns)

        return NodeReturn.branch0