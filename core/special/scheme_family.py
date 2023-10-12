from slither.core.declarations import Contract
from typing import List, Mapping, Tuple
from .scheme import Scheme
from .assemble_scheme import gene_scheme

class SchemeFamily:
    cs:List[Contract]
    name_to_contract:Mapping[str, Contract]
    interface_derived_contracts_by_name:Mapping[str,List[str]]

    name_to_scheme:Mapping[str, Scheme] = {}

    def __init__(self, cs:List[Contract]):
        self.__gene_necessary_info(cs)
        self.cross_readonly_reentrants:List[Tuple[str,str]] = []

    def __gene_necessary_info(self, cs:List[Contract]):
        self.cs = cs
        self.name_to_contract = {}
        for c in cs:
            self.name_to_contract[c.name] = c
        
        interface_derived_contracts_by_name:Mapping[str,List[str]] = {}
        for c in cs:
            for cc in c.derived_contracts:
                if cc.is_interface:
                    if cc.name not in interface_derived_contracts_by_name:
                        interface_derived_contracts_by_name[cc.name] = []
                    if c.name not in interface_derived_contracts_by_name[cc.name]:
                        interface_derived_contracts_by_name[cc.name].append(c.name)
        self.interface_derived_contracts_by_name = interface_derived_contracts_by_name

    def get_scheme(self, cname:str)->Scheme:
        if cname not in self.name_to_scheme:
            c = self.name_to_contract[cname]
            self.name_to_scheme[cname] = gene_scheme(c)
        return self.name_to_scheme[cname]