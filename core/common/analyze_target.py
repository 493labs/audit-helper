from typing import Mapping, Union
from .e import Chain
from slither.core.declarations import Contract
from slither.core.variables.state_variable import StateVariable
from dataclasses import dataclass
from eth_typing.evm import ChecksumAddress

@dataclass
class SingleTarget:
    chain: Chain = Chain.Eth
    address: ChecksumAddress = None

    name: str = ''
    c: Contract = None
    state_value: Mapping[StateVariable, Union[ChecksumAddress,int]] = None

    is_eoa:bool = False

