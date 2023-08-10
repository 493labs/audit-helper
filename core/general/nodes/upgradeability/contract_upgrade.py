from typing import List
from slither.core.declarations import Contract
from slither.slithir.operations import SolidityCall, LowLevelCall
from slither.core.variables.state_variable import StateVariable
from core.frame.contract_info import ContractInfo

from ...base_node import ContractDecisionNode, NodeReturn

class ContractUpgradeNode(ContractDecisionNode):
    
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
    
    
    def check_initialize_controlled(self, impl_c: Contract) -> int:
        for f in impl_c.functions_entry_points:
            if f.name == 'initialize':
                for modifier in f.modifiers:
                    if modifier.name == 'initializer':
                        return 0
                return 1
        return 2
    
    
    def check_missing_disableInitializers(self, impl_c: Contract) -> bool:
        if impl_c.constructor:
            for internal_call in impl_c.constructor.internal_calls:
                if internal_call.name == '_disableInitializers':
                    return False
        return True
        

    def contract_check(self, contract_info: ContractInfo) -> NodeReturn:
        
        if contract_info.c.is_upgradeable:
            # 实现合约构造函数检查
            state = self.check_missing_disableInitializers(contract_info.c)
            if state:
                self.add_warn('实现合约构造函数没有_disableInitializers')
            else:
                self.add_info('实现合约构造函数有_disableInitializers')
        
            # 实现合约初始化方法检查
            state = self.check_initialize_controlled(contract_info.c)
            if state == 0:
                self.add_info('实现合约initialize方法可控')
            if state == 1:
                self.add_warn('实现合约initialize方法存在被多次初始化风险')
            if state == 2:
                self.add_warn('实现合约不存在initialize方法')
            
            # 实现合约初始化状态检查
            states = self.check_impl_state_init(contract_info.c)
            if len(states) == 0:
                self.add_info('实现合约在部署时未对状态变量进行初始化')
            else:
                state_names = ','.join([state.name for state in states])
                self.add_warn(f'实现合约在部署时对状态变量{state_names}进行了初始化')

        if contract_info.c.is_upgradeable_proxy:
            # 代理合约状态检查
            states = self.check_proxy_state(contract_info.c)
            if len(states) == 0:
                self.add_info('代理合约中不存在状态变量')
            else:
                state_names = ','.join([state.name for state in states])
                self.add_warn(f'代理合约中存在状态变量{state_names}')
                    
        return NodeReturn.branch1


        
