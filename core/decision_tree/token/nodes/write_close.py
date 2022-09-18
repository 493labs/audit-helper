from typing import List
from ..common.base_node import DecisionNode, NodeReturn
from ..common.standard import *

class CloseCheckNode(DecisionNode):
    def check(self, token_info:TokenInfo) -> List[str]:

        def check_close(state_e:Enum, func_es:List[Enum])->List[Function]:
            funcs = token_info.enum_to_state_to_funcs(state_e)
            funcs_required = [token_info.get_f(func_e) for func_e in func_es]   
            return [f for f in funcs if f not in funcs_required]

        funcs_accident = check_close(ERC20_E_view.balanceOf,[ERC20_E_Require.transfer, ERC20_E_Require.transferFrom])
        funcs_accident.extend(check_close(ERC20_E_view.allowance,[ERC20_E_Require.approve, ERC20_E_Require.transferFrom]))

        if len(funcs_accident) == 0:
            self.layerouts.append(f'没有非标准方法对{token_info.state_map[ERC20_E_view.allowance]}或者{token_info.state_map[ERC20_E_view.balanceOf]}具有写入操作')
            return NodeReturn.branch0
        else:
            fnames = ','.join([f.name for f in funcs_accident])
            self.layerouts.append(f'非标准方法{fnames}对{token_info.state_map[ERC20_E_view.allowance]}或者{token_info.state_map[ERC20_E_view.balanceOf]}具有写入操作')
            self.layerouts.append(f'暂未对非标准方法写入balance和allowance的情况进行分析')
            return NodeReturn.reach_leaf

