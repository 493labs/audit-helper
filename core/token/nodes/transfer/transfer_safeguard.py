from typing import List, Union
from enum import Enum

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, TokenInfo

from slither.core.declarations import Function, FunctionContract
from slither.slithir.operations import HighLevelCall, LowLevelCall

class TransferSafeGuardCheck(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        funcs:List[Function] = []
        if token_info.is_erc20:
            funcs = [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom]
        
        for func in funcs:
            func_t = token_info.get_f(func)
            for ir in func_t.all_slithir_operations():
                if isinstance(ir, Union[LowLevelCall, HighLevelCall]):
                    # 如果调用自身方法，则ir.function有可能是一个变量
                    # ECOx
                    # ERC20Pausable(_self).pauser();
                    # address public pauser;
                    if not isinstance(ir.function, Function):
                        continue
                    if ir.function.contract_declarer.kind == "library":
                        # library不算外部调用
                        continue
                    self.add_warn(f"{func.name} 方法中执行了外部调用 {ir.node.expression}，转账方法中可能存在守卫合约进行拦截过滤")
 
        if len(self.layerouts) == 0:
            self.add_info('转账方法中没有守卫合约进行拦截过滤')
        return NodeReturn.branch0