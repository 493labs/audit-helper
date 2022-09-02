from .common.check_base import Erc20BaseCheck, Erc721BaseCheck
from .checks.close_check import erc20_check_close, erc721_check_close, check_asm_s
from .checks.fake_recharge import erc20_check_fake_recharge
from .checks.overflow_check import erc20_check_overflow
from .checks.external_call import erc20_check_external_call, erc721_check_external_call
from .checks.standard_func_check import erc20_check_standard_func, erc721_check_standard_func
from slither.core.declarations import Contract

from .token_identify import identify_token
from core.common.e import TokenType
from .common.output import token_check_output

def check_token(c: Contract):
    token_type = identify_token(c)
    token_check_output.set_token_type(token_type)
    if token_type == TokenType.ERC20:
        check_erc20(c)
    elif token_type == TokenType.ERC721:
        check_erc721(c)

def check_erc20(c:Contract):
    b = Erc20BaseCheck(c)
    erc20_check_close(b)
    check_asm_s(b)
    erc20_check_standard_func(b)
    erc20_check_external_call(b)
    erc20_check_overflow(b)
    erc20_check_fake_recharge(b)

def check_erc721(c:Contract):
    b = Erc721BaseCheck(c)
    erc20_check_close(b)
    check_asm_s(b)
    erc20_check_standard_func(b)
    erc20_check_external_call(b)
