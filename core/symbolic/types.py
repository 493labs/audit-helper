import z3
from typing import Union

class Flag:
    is_symbolic: bool
    def __init__(self, is_symbolic) -> None:
        self.is_symbolic = is_symbolic

# class SolUint(Flag):
#     v: Union[z3.BitVecRef, int] 
#     def __init__(self, v, is_symbolic) -> None:
#         super().__init__(is_symbolic)
#         self.v = v
class SolUint(int):  
    pass  

class SolAddress(int):
    pass

class SolBytes:
    pass