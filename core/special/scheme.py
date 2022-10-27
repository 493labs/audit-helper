from typing import Mapping, Union
from ..utils.url import Chain
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from dataclasses import dataclass
from eth_typing.evm import ChecksumAddress
from core.utils.scan_api import get_sli_c, get_sli_c_by_addr

@dataclass
class BaseInfo:
    chain: Chain = None
    address: ChecksumAddress = None
    code_dir: str = None
    contract_path: str = None
    contract_name: str = None
    c: Contract = None

    def get_c(self)-> Contract:
        if self.c:
            return self.c
        if all([self.code_dir, self.contract_path, self.contract_name]):
            self.c = get_sli_c(self.code_dir, self.contract_path, self.contract_name)
            return self.c
        if all([self.chain, self.address]):
            self.c = get_sli_c_by_addr(self.chain, self.address)
            return self.c
        assert False, f'缺少信息，无法生成c'

@dataclass
class ManageableInfo(BaseInfo):
    admin: ChecksumAddress = None
