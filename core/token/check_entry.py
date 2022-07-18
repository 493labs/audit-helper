from .common.check_base import Erc20BaseCheck, Erc721BaseCheck
from .checks.close_check import erc20_check_close, erc721_check_close, check_asm_s
from .checks.fake_recharge import erc20_check_fake_recharge
from .checks.overflow_check import erc20_check_overflow
from .checks.external_call import erc20_check_external_call, erc721_check_external_call
from .checks.standard_func_check import erc20_check_standard_func, erc721_check_standard_func
from slither.core.declarations import Contract

from .token_identify import identify_token
from core.base.e import TokenType

def check_token(c: Contract):
    token_type = identify_token(c)
    if token_type == TokenType.ERC20:
        print('It is an erc20 token')
        check_erc20(c)
    elif token_type == TokenType.ERC721:
        print('It is an erc721 token')
        check_erc721(c)
    else:
        print(' the token\'s type is unknown')

def check_erc20(c:Contract):
    b = Erc20BaseCheck(c)
    print('-----------------check start-----------------')
    print('--------封闭性检查--------')
    erc20_check_close(b)
    check_asm_s(b)
    print('--------标准方法读写检查--------')
    erc20_check_standard_func(b)
    print('--------写重要状态的方法外部调用检查--------')
    erc20_check_external_call(b)
    print('--------溢出检查--------')
    erc20_check_overflow(b)
    print('--------假充值检查--------')
    erc20_check_fake_recharge(b)
    print('-----------------check end-----------------')

def check_erc721(c:Contract):
    b = Erc721BaseCheck(c)
    print('-----------------check start-----------------')
    print('--------封闭性检查--------')
    erc721_check_close(b)
    check_asm_s(b)
    print('--------标准方法读写检查--------')
    erc721_check_standard_func(b)
    print('--------写重要状态的方法外部调用检查--------')
    erc721_check_external_call(b)
    print('-----------------check end-----------------')
