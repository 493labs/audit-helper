from hexbytes import HexBytes
from web3 import Web3
from web3.middleware import geth_poa_middleware

from .e import Chain

class ReadSlot:
    def __init__(self, chain: Chain) -> None:
        self.w3 = Web3(Web3.HTTPProvider(chain.url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def read_slot(self, contract_addr:str, slot) -> HexBytes:
        hex_bytes = self.w3.eth.get_storage_at(self.w3.toChecksumAddress(contract_addr), slot)
        return hex_bytes

    def read_mapping_value(self, contract_addr: str, key, point) -> HexBytes:
        '''
        key为 {'s':obj}、{'bs':obj}、{'addrStr':obj}、{'v':obj} 中的一种， 分别对应solidity中的string、bytes、address和值类型 
        point为 mapping 所在的slot
        '''
        checked_addr = self.w3.toChecksumAddress(contract_addr)
        assert isinstance(key, dict), '传入的key的格式不对'
        if 'v' in key:
            pp = self.w3.solidityKeccak(
                ['uint256', 'uint256'], [key['v'], point])
        elif 'addrStr' in key:
            v = self.w3.toInt(hexstr=self.w3.toChecksumAddress(key['addrStr']))
            pp = self.w3.solidityKeccak(['uint256', 'uint256'], [v, point])
        elif 's' in key:
            pp = self.w3.solidityKeccak(
                ['string', 'uint256'], [key['s'], point])
        elif 'bs' in key:
            pp = self.w3.solidityKeccak(
                ['bytes', 'uint256'], [key['bs'], point])
        else:
            assert False, '传入的key的格式不对'
        return self.w3.eth.get_storage_at(checked_addr, pp)
