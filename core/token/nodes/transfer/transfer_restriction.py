from typing import List, Union
from enum import Enum

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, TokenInfo

from slither.core.declarations import Function
from slither.slithir.operations import HighLevelCall, LowLevelCall

class TransferRestrictionCheck(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        funcs:List[Function] = []
        if token_info.is_erc20:
            funcs = [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom]
        
        for func in funcs:
            func_t = token_info.get_f(func)
            for sol_var in func_t.all_solidity_variables_read():
                if sol_var.name == "block.number":
                    self.add_warn(f"{func.name} 方法中读取了block.number全局变量，转账方法可能存在同一个区块同一地址转账次数有限制")
 
        if len(self.layerouts) == 0:
            self.add_info('转账方法中没有同一个区块同一地址转账次数有限制')
        return NodeReturn.branch0