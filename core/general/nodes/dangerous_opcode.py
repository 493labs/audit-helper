from slither.core.declarations import Contract, Function, FunctionContract
from slither.slithir.operations import SolidityCall, LowLevelCall
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo

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


class DangerousOpcodeNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        fnames_for_delegatecall = []
        fnamse_for_sstore = []
        for f in contract_info.c.functions_entry_points:

            if f.compilation_unit.solc_version.startswith(('0.5','0.4')):
                # 早期版本，汇编代码以 inline_asm 形式存在
                for n in f.all_nodes():
                    if n.inline_asm and "delegatecall" in n.inline_asm:
                        fnames_for_delegatecall.append(f.name)
                    if n.inline_asm and "sstore" in n.inline_asm:
                        fnamse_for_sstore.append(f.name)
            else:
                for ir in f.all_slithir_operations():
                    if isinstance(ir,SolidityCall) and ir.function.name.startswith("sstore"):
                        fnamse_for_sstore.append(f.name)
                    if isinstance(ir,SolidityCall) and ir.function.name.startswith("delegatecall"):
                        fnames_for_delegatecall.append(f.name)
                        
                    if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
                        fnames_for_delegatecall.append(f.name)

        if len(fnames_for_delegatecall) == 0 and len(fnamse_for_sstore) == 0:
            self.add_info('未发现直接调用sstore和delegatecall的情况')
        else:
            if len(fnames_for_delegatecall) > 0:
                fnames = ','.join(fnames_for_delegatecall)
                self.add_warn(f'{fnames}调用了危险操作码 delegatecall')
            if len(fnamse_for_sstore) > 0:
                fnames = ','.join(fnamse_for_sstore)
                self.add_warn(f'{fnames}调用了危险操作码 sstore')
        return NodeReturn.reach_leaf
