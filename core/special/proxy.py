from typing import Tuple
from slither.core.declarations import Contract
from slither.slithir.operations import SolidityCall
from eth_typing.evm import HexAddress
from core.common.e import Chain
from core.utils.node_api import ReadSlot

class ProxyMode:
    def is_proxy_mode(self, c:Contract) -> bool:
        for f in c.functions_entry_points:
            if f.is_fallback:
                for ir in f.all_slithir_operations():
                    if isinstance(ir, SolidityCall) and ir.function.name.startswith("delegatecall") :
                        return True
        return False 

    def get_impl_and_admin(self, chain:Chain, address:HexAddress)->Tuple[HexAddress, HexAddress]:
        '''
        返回的顺序为： impl, admin
        '''
        read_slot = ReadSlot(chain)
        impl = read_slot.read_proxy_impl(address)[12:32].hex()
        admin = read_slot.read_proxy_admin(address)[12:32].hex()
        return impl, admin
        # assert self.impl != ZERO_ADDRESS, f'实现地址为零地址'
        # assert self.admin != ZERO_ADDRESS, f'管理员地址为零地址，有可能采用了UUPS代理模式'

    def check_proxy_state(self, proxy_c:Contract)->Tuple[bool,str]:
        states = [state for state in proxy_c.all_state_variables_read if not (state.is_constant or state.is_immutable)]
        if len(states) > 0:
            state_names = [state.name for state in states]
            return False, f'代理合约中存在状态变量{state_names}'
        return True, None

    def check_impl_state_init(self, impl_c: Contract)->Tuple[bool,str]:
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

        if len(initialized_states) > 0:
            record = ','.join([item.name for item in initialized_states])
            return False, f'可升级模式中，实现合约在部署时给状态变量[{record}]进行了赋值，这对代理合约是无效的'
        return True, None

        
        
        