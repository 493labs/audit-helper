from core.erc20.common.check_base import BaseCheck
from core.erc20.checks.close_check import CloseCheck
from core.erc20.checks.fake_recharge import FakeRechargeCheck
from core.erc20.checks.overflow_check import OverflowCheck
from core.erc20.checks.standard_func_check import StandardFuncCheck
from slither.core.declarations import Contract

def check_erc20(c:Contract):
    b = BaseCheck(c)
    close_check = CloseCheck(b)
    print('-----------------check start-----------------')
    close_check.check_close()
    close_check.check_call_other_contract()
    close_check.check_sstore()
    FakeRechargeCheck(b).check_fake_recharge()
    OverflowCheck(b).check_overflow()
    StandardFuncCheck(b).check_standard_func()
    print('-----------------check end-----------------')
