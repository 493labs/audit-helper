from ..common.base_node import DecisionNode, NodeReturn
from ..common.token import TokenInfo, ERC20_E_Require, ERC721_E_Require

from slither.slithir.operations import SolidityCall, LowLevelCall

class BackDoorNode(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
        warns = []
        for f in token_info.c.functions_entry_points:
            if f.compilation_unit.solc_version.startswith(('0.5','0.4')):
                # 早期版本，汇编代码以 inline_asm 形式存在
                for n in f.all_nodes():
                    if n.inline_asm and "delegatecall" in n.inline_asm:
                        warns.append(f'{f.full_name} 存在 delegatecall 调用')
                    if n.inline_asm and "sstore" in n.inline_asm:
                        warns.append(f'{f.full_name} 存在 sstore 调用')
            else:
                for ir in f.all_slithir_operations():
                    if isinstance(ir,SolidityCall) and ir.function.name.startswith(("delegatecall","sstore")):
                        warns.append(f'{f.full_name} 存在 {ir.function.name} 调用')
                        
                    if isinstance(ir, LowLevelCall) and ir.function_name == "delegatecall":
                        warns.append(f'{f.full_name} 存在 delegatecall 调用')
        if len(warns) == 0:
            self.add_info('未发现 delegatecall 和 sstore 操作')
        else:
            self.add_warns(warns)
        return NodeReturn.branch0