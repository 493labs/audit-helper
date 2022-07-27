from slither.core.declarations import Contract, Function, FunctionContract
from slither.slithir.operations import SolidityCall, LowLevelCall


def check_dangerous_opcode(f: Function):
    for ir in f.all_slithir_operations():
        if isinstance(ir,SolidityCall) and ir.function.name.startswith("sstore"):
            print(f" {f.name} 使用了 asm 的 sstore ，功能未知")
        if isinstance(ir,SolidityCall) and ir.function.name.startswith("delegatecall"):
            print(f" {f.name} 使用了 asm 的 delegatecall ，功能未知")
            
        if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
            print(f" {f.name} 使用了 delegatecall ，功能未知")

def check_contract_dangerous_opcode(c: Contract):
    for f in c.functions_entry_points:
        if f.is_constructor:
            continue
        check_dangerous_opcode(f)