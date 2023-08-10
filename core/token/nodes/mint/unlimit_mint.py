from typing import List
import time
from slither.core.solidity_types import ElementaryType, UserDefinedType, MappingType
from slither.core.declarations import Function, SolidityFunction, Contract

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC721_E_view, TokenInfo
from core.utils.node_api import ReadSlot


class UnlimitMint(TokenDecisionNode):

    def read_address(self, mint_f:Function, token_info:TokenInfo):
        for node in mint_f.all_nodes():
            if node.is_conditional(): 
                states_read_in_internal_call = [state for call in node.internal_calls if not isinstance(call, SolidityFunction) for state in call.all_state_variables_read() ]                   
                for state in node.state_variables_read + states_read_in_internal_call:
                    eoa_minters_addr = []
                    # owner mint情况
                    if "address" in str(state.type):
                        read_slot = ReadSlot(token_info.chain)
                        owner_addr = read_slot.read_by_selector(token_info.address, "owner()")[12:32].hex()
                        # 如果 owner_addr 为EOA地址
                        if not read_slot.is_contract(owner_addr):
                            eoa_minters_addr.append(owner_addr)
                    # 'AccessControl.RoleData' 情况
                    if isinstance(state.type, MappingType) and isinstance(state.type.type_to, UserDefinedType) and 'RoleData' in state.type.type_to.type.name:
                        read_slot = ReadSlot(token_info.chain)
                        # 读取MINTER_ROLE信息是否有code
                        #minter_addr = read_slot.read_role(token_info.address,"DEFAULT_ADMIN_ROLE")
                        minter_addr_list = read_slot.read_role(token_info.address,"MINTER_ROLE")                        
                        for minter_addr in minter_addr_list:
                            if not read_slot.is_contract(minter_addr):
                                eoa_minters_addr.append(minter_addr)
                                
                    return eoa_minters_addr
                        
        
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        EOA_minters = []
        unlimit_mint_func:List[Function] = []
        mint_fs = token_info.get_mint_fs()
        for f in mint_fs:
            eoa_minters_addr = self.read_address(f, token_info)
            if eoa_minters_addr:
                EOA_minters.extend(eoa_minters_addr)
                unlimit_mint_func.append(f)
       
        if len(EOA_minters) == 0:
            self.add_info(f'未发现无限mint风险')
        else:
            fnames = ','.join([f.name for f in unlimit_mint_func])
            self.add_warn(f'{fnames} 方法存在无限 mint 的风险')  
                
        return NodeReturn.branch0