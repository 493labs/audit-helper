from typing import List
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import HighLevelCall, LowLevelCall

from ..common.check_base import BaseCheck, Erc20BaseCheck, Erc721BaseCheck
from ..common.output import token_check_output

def check_external_call_when_write_s(b: BaseCheck, ss: List[StateVariable]):
    for f in b.c.functions_entry_points:
        is_contain = False
        for s in ss:
            if s in f.all_state_variables_written():
                is_contain = True
                break
        if not f.is_constructor and is_contain:
            for ir in f.all_slithir_operations():
                if isinstance(ir, LowLevelCall | HighLevelCall):
                    if ir.function.contract_declarer.kind == "library":
                        # library不算外部调用
                        continue
                    token_check_output.add_external_check(f" {f.name} 方法中执行的的 {ir.node.expression} 存在外部调用风险")

def erc20_check_external_call(b: Erc20BaseCheck):
    check_external_call_when_write_s(b, [b.allowance, b.balance])

def erc721_check_external_call(b: Erc721BaseCheck):
    check_external_call_when_write_s(b, [b.owners, b.balances, b.operatorApprovals, b.tokenApprovals])