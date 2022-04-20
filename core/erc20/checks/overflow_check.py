from slither.slithir.operations import Binary,BinaryType

from core.erc20.common.check_base import BaseCheck
from core.erc20.common.e import *

class OverflowCheck:
    def __init__(self, b:BaseCheck) -> None:
        self.b = b

    
    def check_overflow(self):
        '''
        溢出检查  
        1. 编译器版本高于0.8.0  
        2. 使用库，这样的话，合约中并没有算术运算（只检查标准方法） 
        '''
        if self.b.c.compilation_unit.solc_version >= "0.8.0":
            return
        
        funcs = []
        # for f in set(self.funcs_write_allowance + self.funcs_write_balance):
        #     funcs.extend(self._func_to_reachable_funcs(f))
        for func in self.b.func.values():
            funcs.extend(self.b.func_to_full_reachable_internal_funcs(func))
        funcs = list(set(funcs))
        for f in funcs:
            for n in f.nodes:
                for ir in n.irs:
                    if isinstance(ir, Binary) and ir.type in[
                        BinaryType.ADDITION,
                        BinaryType.SUBTRACTION,
                        BinaryType.MULTIPLICATION,
                        BinaryType.POWER
                    ]:
                        # if isinstance(ir.variable_left,Variable) and isinstance(ir.variable_right,Variable):
                        print(" {} : {} : {} 存在溢出风险".format(f.contract_declarer.name,f.name,n.expression))
                        break
