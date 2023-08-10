from enum import Enum
from typing import List, Tuple
from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import TokenInfo, ERC20_E_Require, ERC20_E_Extend, ERC20_Event, ERC721_E_Require, ERC721_E_Extend, ERC721_Event

from slither.core.declarations import Function
from slither.slithir.operations import EventCall

def _check(token_info:TokenInfo, items:List[Tuple[Enum, List[Enum], List[Enum]]]) -> List[str]:
    layerouts = []
    for item in items:
        funcs = [token_info.get_f(func_e) for func_e in item[1]]
        if len(item[2]) > 0:
            for func_e in item[2]:
                if not token_info.get_f(func_e) is None:
                    funcs.append(token_info.get_f(func_e))
        for func in funcs:
            func_events = [op.name for op in func.all_slithir_operations() if isinstance(op, EventCall) ]
            if not item[0].value in func_events:
                layerouts.append(f'{func.name} 未正常发送 {item[0].value} 事件')
    return layerouts


class EventNode(TokenDecisionNode):
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        if token_info.is_erc20:
            items = [
                (ERC20_Event.tranfer, [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom], [ERC20_E_Extend.burn, ERC20_E_Extend.burnFrom]),
                (ERC20_Event.approval, [ERC20_E_Require.approve, ERC20_E_Require.transferFrom], [ERC20_E_Extend.burnFrom, ERC20_E_Extend.increaseAllowance, ERC20_E_Extend.decreaseAllowance])
            ]
        elif token_info.is_erc721:
            items = [
                (ERC721_Event.tranfer, [ERC721_E_Require.transferFrom, ERC721_E_Require.safeTransferFrom, ERC721_E_Require.safeTransferFrom2], [ERC721_E_Extend.burn]),
                (ERC721_Event.approval, [ERC721_E_Require.approve], []),
                (ERC721_Event.approvalForAll, [ERC721_E_Require.setApprovalForAll], [])
            ]
            
        layerouts = _check(token_info, items)
        
        if len(layerouts) == 0:
            self.add_info(f'未发现未发送Tranfer/Approval事件的方法')
        else:
            self.add_warns(layerouts)
        return NodeReturn.branch0