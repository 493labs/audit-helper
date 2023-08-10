from typing import List
from slither.core.declarations import Contract, Function
from slither.slithir.operations import HighLevelCall, LowLevelCall
from slither.core.variables.state_variable import StateVariable
from core.frame.contract_info import ContractInfo

from ...base_node import ContractDecisionNode, NodeReturn

class ReentrancyNode(ContractDecisionNode):
    
    def has_nonReentrant_mechanism(self, f:Function) -> bool:
        # 是否具有防重入机制
        for m in f.modifiers:
            if m.name == 'nonReentrant':
                return True
        return False
    
    def check_reentrant(self, c: Contract) -> set[str]:
        reentrant_funcs = []
        for f in c.functions_entry_points:
            if f.is_constructor or f.name == 'initialize' or f.view or f.pure:
                continue
            for ir in f.all_slithir_operations():
                # 1- lowlevelcall 
                # 2- highlevelcall: callback method
                if (isinstance(ir, LowLevelCall) or isinstance(ir, HighLevelCall)):
                    # 写入状态变量并且没有nonReentrant modifier保护
                    if f.all_state_variables_written() and not self.has_nonReentrant_mechanism(f):
                        reentrant_funcs.append(f.canonical_name)
        return set(reentrant_funcs)
                        
    def check_cross_funcs_reentrant(self, c: Contract) -> List[set]:
        reentrant_cross_funcs = []
        for f_a in c.functions_entry_points:
            if f_a.is_constructor or f_a.name == 'initialize' or f_a.view or f_a.pure:
                continue
            for ir in f_a.all_slithir_operations():
                # 1- lowlevelcall 
                # 2- highlevelcall: callback method
                if (isinstance(ir, LowLevelCall) or isinstance(ir, HighLevelCall)):
                    # 写入状态变量并且没有nonReentrant modifier保护
                    if f_a.all_state_variables_written() and not self.has_nonReentrant_mechanism(f_a):
                        reentrant_cross_func: set = {f_a.canonical_name}
                        # function_a存在重入风险，找到另外的函数function_b写入了一样的state_variable
                        for state_var in f_a.all_state_variables_written():
                            for f_b in c.functions_entry_points:
                                if f_b.is_constructor or f_b.name == 'initialize' or f_b.view or f_b.pure:
                                    continue
                                if state_var in f_b.all_state_variables_written():
                                    reentrant_cross_func.add(f_b.canonical_name)
                                    break
                        if len(reentrant_cross_func) > 1 and reentrant_cross_func not in reentrant_cross_funcs:
                            reentrant_cross_funcs.append(reentrant_cross_func)
        return reentrant_cross_funcs
    
    
    def contract_check(self, contract_info: ContractInfo) -> NodeReturn:
        layerouts = []
        # 1. 单函数重入
        reentrant_funcs = self.check_reentrant(contract_info.c)
        for f in reentrant_funcs:
            layerouts.append(f'{f} 方法存在重入攻击的风险')
            
        # 2. 跨函数重入
        reentrant_cross_funcs = self.check_cross_funcs_reentrant(contract_info.c)
        for reentrant_cross_func in reentrant_cross_funcs:
            func_names = ','.join([func for func in reentrant_cross_func])            
            layerouts.append(f'{func_names} 方法存在跨函数重入的风险')
        
        if len(layerouts) == 0:
            self.add_info(f'未发现重入的方法')
        else:
            self.add_warns(layerouts)
        
        return NodeReturn.branch0

