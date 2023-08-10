from typing import List, Tuple
from ..base_node import TokenDecisionNode, NodeReturn
from ..token_info import *


class CloseCheckNode(TokenDecisionNode):
    
    def _check(self, token_info:TokenInfo, items:List[Tuple[Enum, List[Enum], List[Enum]]]) -> List[str]:
        layerouts = []
        for item in items:
            funcs = token_info.enum_to_state_to_funcs(item[0])
            funcs_required = [token_info.get_f(func_e) for func_e in item[1]]   
            funcs_extend = []
            if len(item) > 2:
                funcs_extend = [token_info.get_f(func_e) for func_e in item[2]]
            funcs_accident = [f for f in funcs if f not in funcs_required and f not in funcs_extend]
            if len(funcs_accident) > 0:
                fnames = ','.join([f.name for f in funcs_accident])
                layerouts.append(f'非标准方法 {fnames} 对 {token_info.state_map[item[0]].name} 具有写入操作')    
        return layerouts


    def token_check(self, token_info:TokenInfo) -> NodeReturn:

        if token_info.is_erc20:
            items = [
                (ERC20_E_view.balanceOf, [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom], [ERC20_E_Extend.burn, ERC20_E_Extend.burnFrom]),
                (ERC20_E_view.allowance, [ERC20_E_Require.approve, ERC20_E_Require.transferFrom], [ERC20_E_Extend.burnFrom, ERC20_E_Extend.increaseAllowance, ERC20_E_Extend.decreaseAllowance])
            ]
        elif token_info.is_erc721:
            items = [
                (ERC721_E_view.balanceOf, [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
                (ERC721_E_view.ownerOf, [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
                (ERC721_E_view.getApproved, [ERC721_E_Require.approve, ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
                (ERC721_E_view.isApprovedForAll, [ERC721_E_Require.setApprovalForAll])
            ]
        layerouts = self._check(token_info, items)
        if len(layerouts) == 0:
            state_names = ','.join([token_info.state_map[item[0]].name for item in items])
            self.add_info(f'没有非标准方法对 {state_names} 具有写入操作')
        else:
            self.add_warns(layerouts)
        return NodeReturn.branch0

