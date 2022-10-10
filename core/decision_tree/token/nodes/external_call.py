from enum import Enum
from typing import List, Union
from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import TokenInfo, ERC20_E_view, ERC721_E_view

from slither.core.declarations import Function
from slither.slithir.operations import HighLevelCall, LowLevelCall

class ExternalCallNode(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
        def get_funcs(e:type[Enum])->List[Function]:
            funcs = []
            for ee in e._member_map_.values():
                for func in token_info.enum_to_state_to_funcs(ee):
                    if func.is_constructor:
                        continue
                    if func not in funcs:
                        funcs.append(func)
            return funcs

        funcs:List[Function] = []
        if token_info.is_erc20:            
            funcs = get_funcs(ERC20_E_view)
        elif token_info.is_erc721:
            funcs = get_funcs(ERC721_E_view)

        for func in funcs:
            for ir in func.all_slithir_operations():
                if isinstance(ir, Union[LowLevelCall, HighLevelCall]):
                    if ir.function.contract_declarer.kind == "library":
                        # library不算外部调用
                        continue
                    if ir.function_name in ['onERC721Received']:
                        continue
                    self.add_warn(f"{func.full_name} 方法中执行了外部调用 {ir.node.expression}")
 
        if len(self.layerouts) == 0:
            self.add_info('写入重要状态的方法不存在外部调用')
        return NodeReturn.branch0