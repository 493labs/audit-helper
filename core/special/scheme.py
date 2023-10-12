from slither.core.declarations import Contract, Function
from typing import List

class Scheme:
    def __init__(self, c:Contract):
        self.c = c
        self.readonly_reentrant_analyzed = False
        self.readonly_reentrant_risk_funcs:List[Function] = []
