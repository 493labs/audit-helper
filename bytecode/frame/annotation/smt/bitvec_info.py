from enum import Enum
from typing import Optional, List
from mythril.laser.smt import BitVec

class BitvecInfoType(Enum):
    SourceInfo = 1
    PossibleValueInfo = 2

class BitvecSourceType(Enum):
    Storage = 0

def get_slot_source(bitvec:BitVec)->Optional[BitVec]:
    for annotation in bitvec.annotations:
        if annotation[0] == BitvecInfoType.SourceInfo and annotation[1] == BitvecSourceType.Storage:
            return annotation[2]
    return None

class PossibleValue:
    @staticmethod
    def get_possible_values(bitvec:BitVec)->Optional[List[BitVec]]:
        for annotation in bitvec.annotations:
            if annotation[0] == BitvecInfoType.PossibleValueInfo:
                return annotation[1]
        return None
    
    @staticmethod
    def add_possible_value(bitvec:BitVec, new_value:BitVec):
        for annotation in bitvec.annotations:
            if annotation[0] == BitvecInfoType.PossibleValueInfo:
                annotation[1].append(new_value)
                return


