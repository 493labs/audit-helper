from dataclasses import dataclass
from enum import unique, Enum
from typing import List, Mapping, Union
from slither.core.declarations import Contract, Function
from slither.core.variables.state_variable import StateVariable
from eth_typing.evm import ChecksumAddress

from core.common.e import Chain

@unique
class ERC20_E_view(Enum):
    totalSupply = "totalSupply()"
    balanceOf = "balanceOf(address)"
    allowance = "allowance(address,address)"

@unique
class ERC20_E_Require(Enum):
    transfer = "transfer(address,uint256)"
    approve = "approve(address,uint256)"
    transferFrom = "transferFrom(address,address,uint256)"

@unique
class ERC20_E_Extend(Enum):
    burn = "burn(uint256)"
    burnFrom = "burnFrom(address,uint256)"
    increaseAllowance = "increaseAllowance(address,uint256)"
    decreaseAllowance = "decreaseAllowance(address,uint256)"

@unique
class ERC721_E_view(Enum):
    balanceOf = "balanceOf(address)"
    ownerOf = "ownerOf(uint256)"
    getApproved = "getApproved(uint256)"
    isApprovedForAll = "isApprovedForAll(address,address)"

@unique
class ERC721_E_Require(Enum):
    safeTransferFrom = "safeTransferFrom(address,address,uint256,bytes)"
    safeTransferFrom2 = "safeTransferFrom(address,address,uint256)"
    transferFrom = "transferFrom(address,address,uint256)"
    approve = "approve(address,uint256)"
    setApprovalForAll = "setApprovalForAll(address,bool)"


class TokenInfo:
    c: Contract = None
    chain: Chain = None
    address: ChecksumAddress = None
    proxy_c: Contract = None
    '''
    用于代理模式
    '''
    
    is_erc20: bool = False
    is_erc721: bool = False
    
    func_map:Mapping[Enum, Function] = {}
    state_map:Mapping[Enum, StateVariable] = {}
    state_to_funcs_map:Mapping[StateVariable, List[Function]] = {}
    '''
    状态变量到对它有写入操作的公共方法列表
    '''

    def get_f(self, e:Enum)->Function:
        if e not in self.func_map:
            self.func_map[e] = self.c.get_function_from_signature(e.value)
        return self.func_map[e]

    def state_to_funcs(self,state: StateVariable)->List[Function]:
        if state not in self.state_to_funcs_map:
            self.state_to_funcs_map[state] = [f for f in self.c.functions_entry_points if not f.is_constructor and state in f.all_state_variables_written()]
        return self.state_to_funcs_map[state]

    def enum_to_state_to_funcs(self, e:Enum)->List[Function]:
        # if e not in self.state_map:
        #     return None
        return self.state_to_funcs(self.state_map[e])