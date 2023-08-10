import re

from slither.core.declarations import Function, FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import EventCall
from slither.core.solidity_types import ElementaryType

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import TokenInfo


class PausableCheck(TokenDecisionNode):
    
    def read_in_internalcall(self, s: StateVariable, ic: FunctionContract) -> bool:
        for state in ic.state_variables_read:
            if s == state:
                return True
        if ic.internal_calls:
            for iic in ic.internal_calls:
                if isinstance(iic, FunctionContract):
                    return self.read_in_internalcall(s, iic)
        
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        pause_states = [s for s in token_info.c.state_variables \
            if isinstance(s.type, ElementaryType) \
                and s.type.type == 'bool' \
                    and re.search(r"(?i).*(pause).*", s.name)
        ]
        if len(pause_states) == 1:
            for m in token_info.c.modifiers:
                if pause_states[0] in m.state_variables_read:
                    self.add_warn(f'存在全局暂停的风险')
                    return NodeReturn.branch0
                else:
                    for ic in m.internal_calls:
                        if isinstance(ic, FunctionContract):
                            if self.read_in_internalcall(pause_states[0], ic):
                                self.add_warn(f'存在全局暂停的风险')
                                return NodeReturn.branch0
        elif len(pause_states) == 0:                
            self.add_info(f'未发现全局暂停风险')
            return NodeReturn.branch0
        else:
            self.add_warn(f'全局暂停检查异常')
            return NodeReturn.branch0