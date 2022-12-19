from core.frame.base_node import DecisionNode, NodeReturn
from ..dexpair_info import DexPairInfo, DEX_PAIR_E_Require

class ClassifyNode(DecisionNode):

    def check(self, dexpair_info: DexPairInfo) -> NodeReturn:        
        c = dexpair_info.c        
        f = c.get_function_from_signature(DEX_PAIR_E_Require.swap.value)
        if f and c.is_erc20():
            dexpair_info.f_swap = f
            self.add_info('此为 dex pair 合约')
            return NodeReturn.branch0
        else:
            self.add_focus(f'并非有效的 dex pair 合约')
            return NodeReturn.reach_leaf
