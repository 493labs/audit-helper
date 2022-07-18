from hexbytes import HexBytes
from web3 import Web3
from web3.middleware import geth_poa_middleware

from core.common.e import Chain

class ReadSlot:
    def __init__(self, chain: Chain) -> None:
        self.w3 = Web3(Web3.HTTPProvider(chain.url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def read_slot(self, contract_addr:str, slot) -> HexBytes:
        hex_bytes = self.w3.eth.get_storage_at(self.w3.toChecksumAddress(contract_addr), slot)
        return hex_bytes

    def read_proxy_impl(self, proxy_addr:str) -> HexBytes:
        impl_slot = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
        return self.w3.eth.get_storage_at(self.w3.toChecksumAddress(proxy_addr), impl_slot)

    def read_proxy_admin(self, proxy_addr:str) -> HexBytes:
        admin_slot = '0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103'
        return self.w3.eth.get_storage_at(self.w3.toChecksumAddress(proxy_addr), admin_slot)

    def read_by_selector(self, contract_addr:str, method:str) -> HexBytes:
        return self.w3.eth.call({
            'to': self.w3.toChecksumAddress(contract_addr),
            'data': self.w3.keccak(text = method)[:4].hex()
        })

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
