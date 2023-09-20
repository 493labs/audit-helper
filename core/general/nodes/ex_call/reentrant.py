from typing import List, Optional, Tuple, Set
from slither.core.declarations import Contract, Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

# 对内部调用进行迭代检查
def iter_analyze_function(f:Function)->Tuple[bool, int, List[StateVariable], List[StateVariable]]:
    nodes = f.nodes_ordered_dominators
    has_external_call = False
    state_variables_read_pre:List[StateVariable] = []
    state_variables_written_post:List[StateVariable] = []
    for i in range(len(nodes)):
        node = nodes[i]
        state_variables_read_pre.extend(node.state_variables_read)
        internal_calls = [c for c in node.internal_calls if isinstance(c, Function)]
        if internal_calls:
            assert len(internal_calls) == 1 # 假设一个node只有一个internal_call            
            c = internal_calls[0]
            c_has_external_call,_ ,c_state_variables_read_pre,c_state_variables_written_post  = iter_analyze_function(c)
            state_variables_read_pre.extend(c_state_variables_read_pre)
            if c_has_external_call:
                has_external_call = True
                state_variables_written_post.extend(c_state_variables_written_post)
                break 

        if [name for (_,name) in node.low_level_calls if name != "staticcall" ] \
                or [f for (_,f) in node.high_level_calls if not f.view and not f.pure]:
            has_external_call = True
            break #存在多次外部调用时，只检查第一次

    for j in range(i,len(nodes)):
        node = nodes[j]
        state_variables_written_post.extend(node.state_variables_written)
        internal_calls = [c for c in node.internal_calls if isinstance(c, Function)]
        if internal_calls:
            assert len(internal_calls) == 1 # 假设一个node只有一个internal_call            
            c = internal_calls[0]
            state_variables_written_post.extend(c.all_state_variables_written())
    return has_external_call, i, list(set(state_variables_read_pre)), list(set(state_variables_written_post))

class ReentrantNode(DecisionNode):

    def check(self, contract_info: ContractInfo) -> NodeReturn:
        # 不能基于f.all_slithir_operations()进行搜索，没有顺序
        for f in contract_info.c.functions_entry_points:
            if f.is_constructor:
                continue
            has_external_call,i,state_variables_read_pre,state_variables_written_post  = iter_analyze_function(f)
            if has_external_call:
                if set(state_variables_read_pre) & set(state_variables_written_post) and not self._has_nonReentrant_mechanism(f):
                    self.add_warn(f'{f.name} 的 {f.nodes_ordered_dominators[i].expression} 存在针对自身的重入风险')

                f:FunctionContract = f
                for ff in f.contract.functions_entry_points:
                    if ff == f or ff.is_constructor or ff.pure or self._has_nonReentrant_mechanism(ff):
                        continue
                    if set(state_variables_written_post) & set(ff.all_state_variables_read()):
                        if ff.view:
                            self.add_warn(f'{f.name} 的 {f.nodes_ordered_dominators[i].expression} 存在针对 {ff.name} 的只读重入风险')
                        else:
                            self.add_warn(f'{f.name} 的 {f.nodes_ordered_dominators[i].expression} 存在针对 {ff.name} 的重入风险')
        return NodeReturn.branch0
        
    def _has_nonReentrant_mechanism(self, f:Function) -> bool:
        '''
        是否具有防重入机制
        '''
        for m in f.modifiers:
            if m.name == 'nonReentrant':
                return True
        return False
