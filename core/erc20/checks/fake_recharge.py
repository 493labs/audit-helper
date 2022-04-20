from slither.core.declarations import  Function
from slither.slithir.operations import InternalCall,Return
from slither.slithir.variables import Constant

from core.erc20.common.check_base import BaseCheck
from core.erc20.common.e import *

class FakeRechargeCheck:
    def __init__(self, b:BaseCheck) -> None:
        self.b = b

    def _check_fake_recharge(self, f:Function):
        intercall_irs = []
        for n in f.nodes:
            for ir in n.irs:
                if isinstance(ir, InternalCall):
                    intercall_irs.append(ir)
                if isinstance(ir, Return):
                    ret_value = ir.values[0]
                    if type(ret_value) == Constant:                    
                        if ret_value == False:
                            print("存在假充值风险")
                    else:
                        for intercall_ir in intercall_irs:
                            the_ir:InternalCall = intercall_ir
                            if the_ir.lvalue == ret_value:
                                self._check_fake_recharge(the_ir.function)

    def check_fake_recharge(self):
        '''
        假充值检查
        '''
        self._check_fake_recharge(self.b.func[E.transfer])
