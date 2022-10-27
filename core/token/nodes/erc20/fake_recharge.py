from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, TokenInfo

from slither.core.declarations import  Function
from slither.slithir.operations import InternalCall,Return
from slither.slithir.variables import Constant


class FakeRecharge(TokenDecisionNode):

    def _check_fake_recharge(self, f: Function) -> bool:
        intercall_irs = []
        for n in f.nodes:
            for ir in n.irs:
                if isinstance(ir, InternalCall):
                    intercall_irs.append(ir)
                if isinstance(ir, Return):
                    ret_value = ir.values[0]
                    if type(ret_value) == Constant:                    
                        if ret_value == False:
                            return True
                    else:
                        for intercall_ir in intercall_irs:
                            the_ir:InternalCall = intercall_ir
                            if the_ir.lvalue == ret_value \
                              and self._check_fake_recharge(the_ir.function):
                                return True
        return False


    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        if token_info.is_erc20:
            transfer_fake = self._check_fake_recharge(token_info.get_f(ERC20_E_Require.transfer))
            transfer_from_fake = self._check_fake_recharge(token_info.get_f(ERC20_E_Require.transferFrom))
            if not transfer_fake and not transfer_from_fake:
                self.add_info('假充值检查未见异常')
            if transfer_fake:
                self.add_warn('transfer 方法存在假充值风险')
            if transfer_from_fake:
                self.add_warn('transferFrom 方法存在假充值风险')

        return NodeReturn.branch0