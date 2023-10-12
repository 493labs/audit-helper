from .scheme_family import SchemeFamily
from .multi.cross_readonly_reentrant import cross_readonly_reentrant
from slither.core.declarations import Contract
from typing import List

def gene_scheme_family(cs: List[Contract]) -> SchemeFamily:
    schemeFamily = SchemeFamily(cs)
    cross_readonly_reentrant(schemeFamily)
    return schemeFamily