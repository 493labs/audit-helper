from mythril.laser.smt import BitVec, Bool, If, simplify, symbol_factory

from typing import cast

def slot_to_bitvec(item)->BitVec:
    if isinstance(item, Bool):
        return If(
            cast(Bool, item),
            symbol_factory.BitVecVal(1, 256),
            symbol_factory.BitVecVal(0, 256),
        )
    elif isinstance(item, int):
        return symbol_factory.BitVecVal(item, 256)
    else:
        item = cast(BitVec, item)
        return simplify(item)