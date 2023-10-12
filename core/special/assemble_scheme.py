from .scheme import Scheme
from .single.reentrant import check_readonly_reentrant
from slither.core.declarations import Contract

def gene_scheme(c: Contract) -> Scheme:
    scheme = Scheme(c)
    check_readonly_reentrant(scheme)
    return scheme