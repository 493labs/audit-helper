from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo

from slither.core.declarations import Function, SolidityVariableComposed
from slither.slithir.operations import SolidityCall, LowLevelCall
from slither.analyses.data_dependency.data_dependency import is_dependent

class ClassifyNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        c = contract_info.c
        if c.compilation_unit.solc_version.startswith(('0.5','0.4')):
            # 早期版本，汇编代码以 inline_asm 形式存在
            fs = []
            for f in c.functions_entry_points:
                for n in f.all_nodes():
                    if n.inline_asm and "call" in n.inline_asm:
                        fs.append(f)
            if len(fs) > 0:
                fnames = ','.join([ff.name for ff in fs])
                self.add_focus(f'早期版本的代码，在{fnames}的 asm 代码中存在 call 调用，需要人工分析')
                return NodeReturn.reach_leaf

        fs_sc = []
        fs_lc = []        
        for f in c.functions_entry_points:
            if f.is_fallback:
                continue

            def dependents(v) -> bool:
                for param in f.parameters:
                    if is_dependent(v, param, c):
                        return True
                return False
                
            for ir in f.all_slithir_operations():
                if isinstance(ir,SolidityCall) and ir.function.name.startswith("call"):
                    # 在fallback方法的asm中，ir.arguments的个数为0，不清楚原因。在gnosis的fallback方法中发现此问题
                    if dependents(ir.arguments[1]):
                        fs_sc.append(f)
                        break
                if isinstance(ir, LowLevelCall) and ir.function_name == "call":
                    if dependents(ir.destination):
                        fs_lc.append(f)
                        break
        if fs_sc:
            fnames = ','.join([ff.name for ff in fs_sc])
            self.add_info(f'在{fnames}的 asm 代码中存在 call 调用，且to地址依赖外部输入')
        if fs_lc:
            fnames = ','.join([ff.name for ff in fs_lc])
            self.add_info(f'在{fnames}中存在低级别的 call 调用，且目标地址依赖外部输入')

        if fs_sc or fs_lc:
            fs = fs_sc + fs_lc
            fs_timer = []
            for f in fs:
                f: Function = f
                if SolidityVariableComposed('block.timestamp') in f.all_solidity_variables_read():
                    fs_timer.append(f)
            if fs_timer:
                fnames = ','.join([ff.name for ff in fs_timer])
                self.add_info(f'在{fnames}中对 block.timestamp 进行了读取，此动态调用具有时间锁特征')

            fs_meta_tx = []
            for f in fs:
                ecrecover_calls = [solidity_call for solidity_call in f.all_solidity_calls() if 'ecrecover' in solidity_call.name]
                ECDSA_recover_calls = [library_call for library_call in f.all_library_calls() if library_call[0].name == 'ECDSA' and library_call[1].name == 'recover']
                if ecrecover_calls or ECDSA_recover_calls:
                    fs_meta_tx.append(f)
            if fs_meta_tx:
                fnames = ','.join([ff.name for ff in fs_meta_tx])
                self.add_info(f'在{fnames}中具有元交易签名验证，此动态调用具有多签特征')

        return NodeReturn.reach_leaf