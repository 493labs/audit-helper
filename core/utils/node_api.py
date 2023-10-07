from typing import List, Tuple
from hexbytes import HexBytes
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_utils.abi import event_signature_to_log_topic

from core.utils.url import Chain

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

# bytes32(uint256(keccak256('eip1967.proxy.admin')) - 1))
ADMIN_SLOT = '0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103'
# bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1))
IMPL_SLOT = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
# bytes32(uint256(keccak256('eip1967.proxy.beacon')) - 1))
BEACON_SLOT = '0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50'

class ReadSlot:
    def __init__(self, chain: Chain) -> None:
        self.w3 = Web3(Web3.HTTPProvider(chain.url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def read_slot(self, contract_addr:str, slot) -> HexBytes:
        return self.w3.eth.get_storage_at(self.w3.toChecksumAddress(contract_addr), slot)

    def read_proxy_impl(self, proxy_addr:str) -> HexBytes:
        return self.read_slot(proxy_addr, IMPL_SLOT)

    def read_proxy_admin(self, proxy_addr:str) -> HexBytes:
        return self.read_slot(proxy_addr, ADMIN_SLOT)
    
    def read_proxy_beacon(self, proxy_addr:str) -> HexBytes:
        return self.read_slot(proxy_addr, BEACON_SLOT)

    def read_by_selector(self, contract_addr:str, method:str) -> HexBytes:
        return self.w3.eth.call({
            'to': self.w3.toChecksumAddress(contract_addr),
            'data': self.w3.keccak(text = method)[:4].hex()
        })
    
    def read_by_slector_args(self, contract_addr:str, method:str, calldata_args:str) -> HexBytes:
        return self.w3.eth.call({
            'to': self.w3.toChecksumAddress(contract_addr),
            'data': self.w3.keccak(text = method)[:4].hex() + calldata_args
        })
    
    def read_role(self, contract_addr:str, ROLE:str)->List[str]:
        role_addr=[]
        if ROLE == "DEFAULT_ADMIN_ROLE":
            role_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
        else:
            role_hash = self.w3.keccak(text = ROLE).hex()
        role_count_hex = self.read_by_slector_args(contract_addr, "getRoleMemberCount(bytes32)", role_hash[2:])
        role_count = self.w3.toInt(role_count_hex)
        for i in range(role_count):
            index = self.w3.toHex(i)[2:].rjust(64,'0')
            calldata_args = role_hash[2:] + index
            role_addr.append(self.read_by_slector_args(contract_addr, "getRoleMember(bytes32,uint256)", calldata_args).hex()[26:])
        return role_addr
            
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

    def _read_role(self, address:str, createBlock:int, role_topic:str)->List[str]:
        filter_Params = {
            'topics':[
                '0x' + event_signature_to_log_topic('RoleGranted(bytes32,address,address)').hex(),
                role_topic
            ],    
            'address':address,
            'fromBlock': createBlock,
        }
        return [log['topics'][2][12:32].hex() for log in self.w3.eth.get_logs(filter_Params)]
    
    def read_role_by_event(self, address:str, createBlock:int, role:str)->List[str]:
        return self._read_role(address, createBlock, '0x' + event_signature_to_log_topic(role).hex())
    
    def read_default_admin_role(self, address:str, createBlock:int)->List[str]:
        return self._read_role(address, createBlock, '0x0000000000000000000000000000000000000000000000000000000000000000')
    
    def read_block_num_by_txhash(self, txhash:str)->Tuple[int, int]:
        txdata = self.w3.eth.get_transaction(txhash)
        return txdata['blockNumber'], txdata['transactionIndex']
    
    def read_sig_by_txhash(self, txhash:str)->Tuple[str, str, str]:
        txdata = self.w3.eth.get_transaction(txhash)
        return txdata['r'], txdata['s'], txdata['v']
    
    def is_contract(self, address:str)->bool:
        code = self.w3.eth.get_code(self.w3.toChecksumAddress(address))
        # https://web3py.readthedocs.io/en/v6.1.0/web3.eth.html#web3.eth.Eth.get_code
        if code == HexBytes("0x"):
            return False
        else:
            return True
            