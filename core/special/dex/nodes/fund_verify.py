from core.frame.base_node import DecisionNode, NodeReturn
from ..dexpair_info import DexPairInfo, DEX_PAIR_E_Require

from slither.core.cfg.node import NodeType
from slither.slithir.operations import Binary, BinaryType

class FundVerifyNode(DecisionNode):

    def check(self, dexpair_info: DexPairInfo) -> NodeReturn: 
        entry_point = dexpair_info.f_swap.entry_point
        last_binary = None
        last_require = None
        cur_node = entry_point
        while cur_node.dominance_exploration_ordered:
            next_node = cur_node.dominance_exploration_ordered[-1]
            if next_node.contains_require_or_assert():
                last_require = next_node
            else:
                if [library_call for library_call in next_node.library_calls if library_call[0].name.lower() == 'safemath']:
                    last_binary = next_node
                elif any(isinstance(ir, Binary) and ir.type in [BinaryType.MULTIPLICATION] for ir in next_node.irs):
                    last_binary = next_node
            cur_node = next_node

        last_binary_start = last_binary.source_mapping['start']
        last_require_start = last_require.source_mapping['start']
        if last_binary_start < last_require_start:
            self.add_info('swap 方法具有最后的校验')
        else:
            self.add_warn('swap 方法缺少最后的校验')
        return NodeReturn.reach_leaf