from enum import unique, Enum
from typing import List, Mapping
from slither.core.declarations import Contract, Function
from slither.slithir.operations import LibraryCall, Binary, BinaryType
from slither.core.variables.state_variable import StateVariable

from core.frame.contract_info import ContractInfo

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
class ERC20_Event(Enum):
    tranfer = "Transfer"
    approval = "Approval"

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

@unique
class ERC721_E_Extend(Enum):
    burn = "burn(uint256)"
    baseuri = "_baseURI()"

@unique
class ERC721_Event(Enum):
    tranfer = "Transfer"
    approval = "Approval"
    approvalForAll = "ApprovalForAll"


class TokenInfo(ContractInfo):
    #proxy_c: Contract = None
    '''
    用于代理模式
    '''
    
    is_erc20: bool = False
    is_erc721: bool = False
    is_erc721a: bool = False
    
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

    def get_mint_fs(self)->List[Function]:
        if self.__mint_fs == None:
            self.__get_mint_burn_fs()
        return self.__mint_fs

    __mint_fs: List[Function] = None
    __burn_fs: List[Function] = None
    def __get_mint_burn_fs(self):
        self.__mint_fs = []
        self.__burn_fs = []

        if self.is_erc20:
            balance_state = self.state_map[ERC20_E_view.balanceOf]
        elif self.is_erc721:
            balance_state = self.state_map[ERC721_E_view.balanceOf]
        else:
            assert False, '未知的 token 类型'

        for f in self.c.functions_entry_points:
            if f.is_constructor:
                continue
            if balance_state not in f.all_state_variables_written():
                continue
            
            have_add_op = False
            for node in f.all_nodes():
                if balance_state in node.state_variables_written:
                    for ir in node.irs:
                        if isinstance(ir, LibraryCall) and ir.function_name == 'add':
                            have_add_op = True
                            break
                        if isinstance(ir, Binary) and ir.type == BinaryType.ADDITION:
                            have_add_op = True
                            break
                if have_add_op:
                    break

            have_sub_op = False
            for node in f.all_nodes():
                if balance_state in node.state_variables_written:
                    for ir in node.irs:
                        if isinstance(ir, LibraryCall) and ir.function_name == 'sub':
                            have_sub_op = True
                            break
                        if isinstance(ir, Binary) and ir.type == BinaryType.SUBTRACTION:
                            have_sub_op = True
                            break
                if have_sub_op:
                    break

            if have_add_op and not have_sub_op:
                self.__mint_fs.append(f)
            if not have_add_op and have_sub_op:
                self.__burn_fs.append(f)
