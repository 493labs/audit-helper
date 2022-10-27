from slither.core.declarations import Contract
from eth_typing.evm import ChecksumAddress

from core.utils.url import Chain

class ContractInfo:
    c: Contract = None
    chain: Chain = None
    address: ChecksumAddress = None
    
    
