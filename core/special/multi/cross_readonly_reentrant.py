from ..scheme_family import SchemeFamily
from assemble_scheme import gene_scheme

def cross_readonly_reentrant(schemeFamily:SchemeFamily):
    '''若外部调用的是一个接口，判断继承该接口的合约是否具有只读重入风险，且调用的方法在风险合约的特定方法中
    '''
    for c in schemeFamily.cs:
        for high_level_call in c.all_high_level_calls:
            call_c, call_f = high_level_call
            if call_c.is_interface and call_c.name in schemeFamily.interface_derived_contracts_by_name:
                for name in schemeFamily.interface_derived_contracts_by_name[call_c.name]:
                    scheme = schemeFamily.get_scheme(name)
                    if call_f.name in scheme.readonly_reentrant_risk_funcs:
                        schemeFamily.cross_readonly_reentrants.append((c.name, name))
