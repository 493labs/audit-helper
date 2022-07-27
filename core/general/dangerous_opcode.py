from slither.core.declarations import Contract, Function, FunctionContract
from slither.slithir.operations import SolidityCall, LowLevelCall


def check_dangerous_opcode(f: Function):
    if f.compilation_unit.solc_version.startswith(('0.5','0.4')):
        # 早期版本，汇编代码以 inline_asm 形式存在
        for n in f.all_nodes():
            if n.inline_asm and "delegatecall" in n.inline_asm:
                print(f" {f.name} 使用了 asm 的 delegatecall ，功能未知")
            if n.inline_asm and "sstore" in n.inline_asm:
                print(f" {f.name} 使用了 asm 的 sstore ，功能未知")
    else:
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