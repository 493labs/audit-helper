from slither.slithir.operations import SolidityCall, LowLevelCall
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo

class DangerousOpcodeNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        fnames_for_delegatecall = []
        fnamse_for_sstore = []
        
        is_old_solc = contract_info.c.compilation_unit.solc_version.startswith(('0.5','0.4'))
        for f in contract_info.c.functions_entry_points:

            if is_old_solc:
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
