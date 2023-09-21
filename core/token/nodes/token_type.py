import sys
import time
from typing import List
from slither.core.declarations import Contract
from slither.slithir.operations import SolidityCall, LowLevelCall
from slither.core.variables.state_variable import StateVariable
from core.utils.node_api import ReadSlot, ZERO_ADDRESS
from core.utils.scan_api import get_sli_c_by_addr

from ..base_node import TokenDecisionNode, NodeReturn
from ..token_info import TokenInfo, ERC20_E_Require, ERC721_E_Require

class TokenTypeNode(TokenDecisionNode):
    
    def is_proxy_mode(self, c:Contract) -> bool:
        for f in c.functions_entry_points:
            if f.is_fallback:
                if f.compilation_unit.solc_version.startswith(('0.5','0.4')):
                    # 早期版本，汇编代码以 inline_asm 形式存在
                    for n in f.all_nodes():
                        if n.inline_asm and "delegatecall" in n.inline_asm:
                            return True
                else:
                    for ir in f.all_slithir_operations():
                        if isinstance(ir,SolidityCall) and ir.function.name.startswith("delegatecall"):
                            return True
                        
                        if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
                            return True      
        return False 

    def check_proxy_state(self, proxy_c:Contract)->List[StateVariable]:
        return [state for state in proxy_c.all_state_variables_read if not (state.is_constant or state.is_immutable)]

    def check_impl_state_init(self, impl_c: Contract)->List[StateVariable]:
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

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        is_erc20 = True
        for e in ERC20_E_Require._member_map_.values():
            if not token_info.c.get_function_from_signature(e.value):
                is_erc20 = False
                break
        if is_erc20:
            token_info.is_erc20 = True
            self.add_info('合约为erc20')
            return NodeReturn.branch0

        is_erc721 = True
        for e in ERC721_E_Require._member_map_.values():
            if not token_info.c.get_function_from_signature(e.value):
                is_erc721 = False
                break
        if is_erc721:
            token_info.is_erc721 = True
            is_erc721a = False
            for cc in token_info.c.inheritance + [token_info.c]:
                if cc.name.lower() == 'erc721a':
                    is_erc721a = True                    
                    break

            if is_erc721a:
                token_info.is_erc721a = True
                self.add_info('合约为erc721a')
            else:
                self.add_info('合约为erc721')
            return NodeReturn.branch0

        if self.is_proxy_mode(token_info.c):
            self.add_info('合约为代理合约')
            if not self.on_chain:
                self.add_warn('进一步分析需要使用链上模式')
                return NodeReturn.reach_leaf

            self.add_info(f'代理合约地址为 {token_info.address}')
            read_slot = ReadSlot(token_info.chain)
            impl = read_slot.read_proxy_impl(token_info.address)[12:32].hex()
            self.add_info(f'代理合约的implementation地址为 {impl}')
            if impl == ZERO_ADDRESS:
                return NodeReturn.reach_leaf

            try:
                # etherscan api 频率限制 5s 一次请求
                time.sleep(6)
                impl_c = get_sli_c_by_addr(token_info.chain, impl)
            except Exception as err:
                tb = sys.exc_info()[2]
                self.add_warn('获取实现合约contract对象失败，原因如下：')
                self.add_warn(str(err))
                return NodeReturn.reach_leaf
            self.add_info('获取实现合约成功，进行进一步分析')
            
            admin = read_slot.read_proxy_admin(token_info.address)[12:32].hex()
            beacon = read_slot.read_proxy_beacon(token_info.address)[12:32].hex()
            if admin != ZERO_ADDRESS:
                self.add_info(f'代理合约为transparent proxy, proxyadmin地址为 {admin}')
                # proxyAdmin owner是否为EOA地址
                proxy_owner_addr = read_slot.read_by_selector(admin, "owner()")[12:32].hex()
                # 如果 owner_addr 为EOA地址
                if not read_slot.is_contract(proxy_owner_addr):
                    self.add_warn(f'代理合约的proxyAdmin owner为EOA地址 {proxy_owner_addr}')
                    
            if beacon != ZERO_ADDRESS:
                self.add_info(f'代理合约为beacon proxy, beacon地址为 {beacon}')
                # beacon owner是否为EOA地址
                beacon_owner_addr = read_slot.read_by_selector(beacon, "owner()")[12:32].hex()
                # 如果 owner_addr 为EOA地址
                if not read_slot.is_contract(beacon_owner_addr):
                    self.add_warn(f'代理合约的beacon owner为EOA地址 {beacon_owner_addr}')

            
            token_info.proxy_c = token_info.c
            token_info.c = impl_c

            # 代理合约状态检查
            states = self.check_proxy_state(token_info.proxy_c)
            if len(states) == 0:
                self.add_info('代理合约中不存在状态变量')
            else:
                state_names = ','.join([state.name for state in states])
                self.add_warn(f'代理合约中存在状态变量{state_names}')
            
            # 实现合约初始化状态检查
            states = self.check_impl_state_init(token_info.c)
            if len(states) == 0:
                self.add_info('实现合约在部署时未对状态变量进行初始化')
            else:
                state_names = ','.join([state.name for state in states])
                self.add_warn(f'实现合约在部署时对状态变量{state_names}进行了初始化')
            
            return NodeReturn.branch1

        self.add_warn(f'未知的合约类型，无法进一步分析')
        return NodeReturn.reach_leaf


        
