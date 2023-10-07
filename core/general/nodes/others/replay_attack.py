from typing import List
import re
from slither.core.declarations import Contract, Function
from slither.slithir.operations import SolidityCall
from core.frame.contract_info import ContractInfo
from core.frame.base_node import DecisionNode,NodeReturn


class ReplayAttackNode(DecisionNode):
    def check_replay_attack(self, c:Contract) ->List[str]:
        replay_attack_funcs = []
        for f in c.functions_entry_points:
            if f.is_constructor and f.name == "initialize" and f.view or f.pure:
                continue
            replay_attack = False
            for ir in f.all_slithir_operations():
                if isinstance(ir, SolidityCall) and ir.function.full_name == "ecrecover(bytes32,uint8,bytes32,bytes32)":
                    replay_attack = True
                    for state_writen in f.all_state_variables_written():
                        if re.search("(?i).*(nonce).*", state_writen.name):
                            replay_attack = False
            if replay_attack:
                replay_attack_funcs.append(f.name)
        return replay_attack_funcs

    def check(self, contract_info=ContractInfo) -> NodeReturn:
        layerouts = []
        replay_attack_funcs = self.check_replay_attack(contract_info.c)
        for f in replay_attack_funcs:
            layerouts.append(f'{f} 方法存在重放攻击的风险')
        if len(layerouts) == 0:
            self.add_info("未发现重放攻击的方法")
        else:
            self.add_warns(layerouts)
        return NodeReturn.branch0
