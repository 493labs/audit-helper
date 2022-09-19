from typing import List, Tuple
from ..common.base_node import DecisionNode, NodeReturn
from ..common.standard import *


def _check(token_info:TokenInfo, items:List[Tuple[Enum, List[Enum]]]) -> Tuple[List[str], NodeReturn]:
    layerouts = []
    for item in items:
        funcs = token_info.enum_to_state_to_funcs(item[0])
        funcs_required = [token_info.get_f(func_e) for func_e in item[1]]   
        funcs_accident = [f for f in funcs if f not in funcs_required]
        if len(funcs_accident) > 0:
            fnames = ','.join([f.name for f in funcs_accident])
            layerouts.append(f'非标准方法 {fnames} 对 {token_info.state_map[item[0]].name} 具有写入操作')
    
    state_names = ','.join([token_info.state_map[item[0]].name for item in items])
    if len(layerouts) == 0:
        return [f'没有非标准方法对 {state_names} 具有写入操作'], NodeReturn.branch0
    else:
        layerouts.append(f'暂未对非标准方法写入 {state_names} 的情况进行分析')
        return layerouts, NodeReturn.reach_leaf

class Erc20CloseCheckNode(DecisionNode):
    def check(self, token_info:TokenInfo) -> NodeReturn:

        items = [
            (ERC20_E_view.balanceOf, [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom]),
            (ERC20_E_view.allowance, [ERC20_E_Require.approve, ERC20_E_Require.transferFrom])
        ]
        layerouts, node_return = _check(token_info, items)
        self.layerouts.extend(layerouts)
        return node_return

class Erc721CloseCheckNode(DecisionNode):
    def check(self, token_info:TokenInfo) -> NodeReturn:

        items = [
            (ERC721_E_view.balanceOf, [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
            (ERC721_E_view.ownerOf, [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
            (ERC721_E_view.getApproved, [ERC721_E_Require.approve, ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2]),
            (ERC721_E_view.isApprovedForAll, [ERC721_E_Require.setApprovalForAll])
        ]
        layerouts, node_return = _check(token_info, items)
        self.layerouts.extend(layerouts)
        return node_return

