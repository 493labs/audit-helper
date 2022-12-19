from enum import unique, Enum
from core.frame.contract_info import ContractInfo

from slither.core.declarations import Function
@unique
class DEX_PAIR_E_Require(Enum):
    swap = 'swap(uint256,uint256,address,bytes)'

class DexPairInfo(ContractInfo):
    f_swap:Function = None