from typing import List
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations import  Function
from slither.slithir.operations import SolidityCall,HighLevelCall,LowLevelCall

from core.erc20.common.check_base import BaseCheck
from core.erc20.common.e import *

class CloseCheck:
    def __init__(self, b:BaseCheck) -> None:
        self.b = b
        self.funcs_write_balance:List[Function] = self.__get_funcs_write_the_state(self.b.balance)
        self.funcs_write_allowance:List[Function] = self.__get_funcs_write_the_state(self.b.allowance)

    def __get_funcs_write_the_state(self, s: StateVariable) -> List[Function]:
        '''
        获取哪些可外部访问的方法对指定state进行了写操作
        '''
        fs = []
        for f in self.b.c.functions_entry_points:
            if not f.is_constructor:
                for ff in self.b.func_to_full_reachable_internal_funcs(f):
                    if s in ff.state_variables_written:
                        fs.append(f)
                        break
        return fs
 
    def check_close(self):
        allow_funcs = [self.b.func[e] for e in [E.transfer, E.transferFrom, E.burn] if e in self.b.func]
        for f in self.funcs_write_balance:
            if f not in allow_funcs:
                print("未知方法 {} 对 {} 进行了写操作".format(f.name, self.b.balance.name))
        
        allow_funcs = [self.b.func[e] for e in [E.approve, E.transferFrom, E.increaseAllowance, E.decreaseAllowance] if e in self.b.func]
        for f in self.funcs_write_allowance:
            if f not in allow_funcs:
                print("未知方法 {} 对 {} 进行了写操作".format(f.name, self.b.allowance.name))

    
    def check_call_other_contract(self):
        '''
        对可写balance和allowance的入口方法进行外部调用检查
        '''
        funcs = []
        for f in set(self.funcs_write_allowance + self.funcs_write_balance):
            funcs.extend(self.b.func_to_full_reachable_internal_funcs(f))
        funcs:List[Function] = list(set(funcs))
        for f in funcs:
            for node in f.nodes:
                for ir in node.irs:
                    if isinstance(ir, LowLevelCall | HighLevelCall):
                        if ir.function.contract_declarer.kind == "library":
                            # library不算外部调用
                            continue
                        print(" {} 方法中的 {} 存在外部调用风险".format(f.name,node.expression))

    def _func_has_asm_sload(self,f:Function) -> bool:
        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, SolidityCall) and ir.function.name == "sload":
                    print(" {} 使用了 asm 的 sload ，功能未知".format(f.name,))
                    return True
        return False
    def _func_has_asm_sstore(self,f:Function) -> bool:
        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, SolidityCall) and ir.function.name == "sstore":
                    print(" {} 使用了 asm 的 sstore ，功能未知".format(f.name,))
                    return True
        return False

    def check_sstore(self):
        '''
        若程序中带有sload和sstore的汇编指令，则其行为具有很大的不确定性
        '''
        funcs = []
        for f in self.b.c.functions_entry_points:
            funcs.extend(self.b.func_to_full_reachable_internal_funcs(f))
        funcs = list(set(funcs))
        for f in funcs:
            self._func_has_asm_sstore(f)
            self._func_has_asm_sload(f)


