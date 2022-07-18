from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import Contract, Function
from slither.core.expressions import MemberAccess, Identifier, TypeConversion

class ExternalCall():
    def __init__(self, c:Contract) -> None:
        self.c = c
        self.writable_entry = list(filter(lambda f:not f.view and not f.pure, c.functions_entry_points))

    def find_dangerous_ex_call(self):
        for f in self.writable_entry:
            for ex_call_expression in f.external_calls_as_expressions:
                called: MemberAccess = ex_call_expression.called
                ex: Identifier
                if isinstance(called.expression, TypeConversion):
                    ex = called.expression.expression
                else:
                    ex = called.expression
                for entry in self.writable_entry:
                    for param in entry.parameters:
                        if is_dependent(ex.value, param, self.c):
                            print("危险的外部调用：{} 中的 {} 依赖于 {} 的参数 {}".format(
                                f.name, ex_call_expression, entry.name, param.name
                            ))


