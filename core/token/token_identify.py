from core.common.e import TokenType
from .common.e import ERC20_E, ERC721_E

from slither.core.declarations import Contract

def identify_token(c: Contract) -> TokenType:
    is_erc20 = True
    for e in ERC20_E._member_map_.values():
        if e.is_required and not c.get_function_from_signature(e.sign):
            is_erc20 = False
            break
    if is_erc20:
        return TokenType.ERC20

    is_erc721 = True
    for e in ERC721_E._member_map_.values():
        if e.is_required and not c.get_function_from_signature(e.sign):
            is_erc721 = False
            break
    if is_erc721:
        return TokenType.ERC721

    return TokenType.OTHER