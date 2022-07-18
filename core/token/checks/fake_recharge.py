from slither.core.declarations import  Function
from slither.slithir.operations import InternalCall,Return
from slither.slithir.variables import Constant

from ..common.check_base import Erc20BaseCheck
from ..common.e import ERC20_E

def _check_fake_recharge(f: Function):
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
                            _check_fake_recharge(the_ir.function)

def erc20_check_fake_recharge(b: Erc20BaseCheck):
        '''
        假充值检查
        '''
        _check_fake_recharge(b.func[ERC20_E.transfer])
        