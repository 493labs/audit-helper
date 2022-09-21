import sys
from typing import List
from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import TokenInfo, ERC20_E_Require, ERC721_E_Require

from slither.core.declarations import Contract
from slither.slithir.operations import SolidityCall
from slither.core.variables.state_variable import StateVariable

from core.utils.read_slot import ReadSlot, ZERO_ADDRESS
from core.utils.source_code import get_sli_c_by_addr

def is_proxy_mode(c:Contract) -> bool:
    for f in c.functions_entry_points:
        if f.is_fallback:
            for ir in f.all_slithir_operations():
                if isinstance(ir, SolidityCall) and ir.function.name.startswith("delegatecall") :
                    return True
    return False 

def check_proxy_state(proxy_c:Contract)->List[StateVariable]:
    return [state for state in proxy_c.all_state_variables_read if not (state.is_constant or state.is_immutable)]

def check_impl_state_init(impl_c: Contract)->List[StateVariable]:
    initialized_states = []
    for s in impl_c.state_variables:
        if s.is_constant or s.is_immutable:
            continue
        if s.initialized:
            if 'int' in s.type.name and s.expression.value == '0':
                continue
            if 'address' in s.type.name and s.expression.expression.value in ['0x0', '0']:
                continue
            if 'bool' in s.type.name and s.expression.value == 'false':
                continue
            initialized_states.append(s)
    return initialized_states

class TokenTypeNode(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
        is_erc20 = True
        for e in ERC20_E_Require._member_map_.values():
            if not token_info.c.get_function_from_signature(e.value):
                is_erc20 = False
                break
        if is_erc20:
            self.layerouts.append('合约为erc20')
            return NodeReturn.branch0

        is_erc721 = True
        for e in ERC721_E_Require._member_map_.values():
            if not token_info.c.get_function_from_signature(e.value):
                is_erc721 = False
                break
        if is_erc721:
            self.layerouts.append('合约为erc721')
            return NodeReturn.branch1

        if is_proxy_mode(token_info.c):
            self.layerouts.append('合约为代理合约')
            if not self.on_chain:
                self.layerouts.append('进一步分析需要使用链上模式')
                return NodeReturn.reach_leaf

            self.layerouts.append(f'代理合约地址为 {token_info.address}')
            read_slot = ReadSlot(token_info.chain)
            impl = read_slot.read_proxy_impl(token_info.address)[12:32].hex()
            admin = read_slot.read_proxy_admin(token_info.address)[12:32].hex()
            self.layerouts.append(f'代理合约的实现地址为 {impl}')
            self.layerouts.append(f'代理合约的管理员地址为 {admin}')
            if impl == ZERO_ADDRESS:
                return NodeReturn.reach_leaf

            try:
                impl_c = get_sli_c_by_addr(token_info.chain, impl)
            except Exception as err:
                tb = sys.exc_info()[2]
                self.layerouts.append('获取实现合约contract对象失败，原因如下：')
                self.layerouts.append(err.with_traceback(tb))
                return NodeReturn.reach_leaf

            self.layerouts.append('获取实现合约成功，进行进一步分析')
            token_info.proxy_c = token_info.c
            token_info.c = impl_c

            # 代理合约状态检查
            states = check_proxy_state(token_info.proxy_c)
            if len(states) == 0:
                self.layerouts.append('代理合约中不存在状态变量')
            else:
                state_names = ','.join([state.name for state in states])
                self.layerouts.append(f'代理合约中存在状态变量{state_names}')
            
            # 实现合约初始化状态检查
            states = check_impl_state_init(token_info.c)
            if len(states) == 0:
                self.layerouts.append('实现合约在部署时未对状态变量进行初始化')
            else:
                state_names = ','.join([state.name for state in states])
                self.layerouts.append(f'实现合约在部署时对状态变量{state_names}进行了初始化')
            
            return NodeReturn.branch2

        self.layerouts.append(f'未知的合约类型，无法进一步分析')
        return NodeReturn.reach_leaf


        
