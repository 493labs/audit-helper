from slither.slithir.operations import Binary,BinaryType
from slither.core.declarations import Function

from ..common.check_base import Erc20BaseCheck
from ..common.e import ERC20_E
from ..common.output import token_check_output

def check_overflow(f: Function):
    '''
    溢出检查  
    1. 编译器版本高于0.8.0  
    2. 使用库，这样的话，合约中并没有算术运算（只检查标准方法） 
    '''
    if f.compilation_unit.solc_version >= "0.8.0":
        return
    
    for ir in f.all_slithir_operations():
        if isinstance(ir, Binary) and ir.type in[
            BinaryType.ADDITION,
            BinaryType.SUBTRACTION,
            BinaryType.MULTIPLICATION,
            BinaryType.POWER
        ]:
            # if isinstance(ir.variable_left,Variable) and isinstance(ir.variable_right,Variable):
            token_check_output.add_overflow_check(f"  {f.name} : {ir.node.expression} 存在溢出风险")

def erc20_check_overflow(b: Erc20BaseCheck):
    check_overflow(b.func[ERC20_E.approve])
    check_overflow(b.func[ERC20_E.transfer])
    check_overflow(b.func[ERC20_E.transferFrom])
    if ERC20_E.burn in b.func:
        check_overflow(b.func[ERC20_E.burn])
    if ERC20_E.increaseAllowance in b.func:
        check_overflow(b.func[ERC20_E.increaseAllowance])
    if ERC20_E.decreaseAllowance in b.func:
        check_overflow(b.func[ERC20_E.decreaseAllowance])
    