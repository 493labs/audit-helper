from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_Require, TokenInfo, ERC20_E_view

from slither.core.declarations import Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.core.solidity_types import MappingType
from slither.slithir.operations import Binary, BinaryType, LibraryCall, SolidityCall
    

class BlackWhiteListCheck(TokenDecisionNode):
    # 
    def func_addr_operation(self, f:Function) -> int:
        addr_map_require_assert = 0 
        for ir in f.all_slithir_operations():
            if isinstance(ir, SolidityCall) and (ir.function.name == 'require(bool,string)' or ir.function.name == 'assert(bool)'):
                for v in ir.node.variables_read:
                    if isinstance(v.type, MappingType):
                        if v.type.type_from.type == "address" or v.type.type_to.type == "address":
                            addr_map_require_assert += 1
            
        return addr_map_require_assert
    
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        func_es = []
        warns = []
        if token_info.is_erc20:
            func_es = [ERC20_E_Require.transfer, ERC20_E_Require.transferFrom]

        for func_e in func_es:
            transfer_func = token_info.get_f(func_e)
            if self.func_addr_operation(transfer_func) > 0:
                warns.append(f'{transfer_func.name} 存在黑白名单风险')
            
        if len(warns) == 0:
            self.add_info(f'未发现黑白名单的设置')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0

