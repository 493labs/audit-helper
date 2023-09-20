from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.expressions import MemberAccess, Identifier, TypeConversion
from core.frame.base_node import DecisionNode,NodeReturn
from core.frame.contract_info import ContractInfo

class ExCallDependOnTxInputNode(DecisionNode):
    
    def check(self, contract_info: ContractInfo) -> NodeReturn:
        writable_entry = list(filter(lambda f:not f.view and not f.pure, contract_info.c.functions_entry_points))
        for f in writable_entry:
            for ex_call_expression in f.external_calls_as_expressions:
                called: MemberAccess = ex_call_expression.called
                ex: Identifier
                if isinstance(called.expression, TypeConversion):
                    ex = called.expression.expression
                else:
                    ex = called.expression
                for entry in writable_entry:
                    for param in entry.parameters:
                        if is_dependent(ex.value, param, contract_info.c):
                            self.add_warn("危险的外部调用：{} 中的 {} 依赖于 {} 的参数 {}".format(
                                f.name, ex_call_expression, entry.name, param.name
                            ))
        return NodeReturn.branch0
