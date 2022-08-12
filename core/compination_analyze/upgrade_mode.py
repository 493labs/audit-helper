from typing import Mapping, Union
from dataclasses import dataclass
from eth_typing.evm import ChecksumAddress
from ..common.analyze_target import SingleTarget


@dataclass
class UpgradeTarget:
    proxy: SingleTarget = None
    impl: SingleTarget = None
    admin: Union[ChecksumAddress, SingleTarget] = None
    
    def check_proxy_state(self):
        if len(self.proxy.c.all_state_variables_read) > 0:
            print(f'可升级模式中，{self.proxy.c.name}代理合约存在状态变量，可能影响实现合约逻辑')

    def check_impl_state_init_point(self):
        initialized_states = []
        for s in self.impl.c.state_variables:
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
            print(f'可升级模式中，{self.impl.c.name}实现合约在部署时给状态变量[{record}]进行了赋值，这对代理合约是无效的')
        

