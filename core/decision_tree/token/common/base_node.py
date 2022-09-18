from abc import ABCMeta, abstractmethod
from enum import Enum, unique
from typing import List
from .standard import TokenInfo

@unique
class NodeReturn(Enum):
    reach_leaf = -1
    branch0 = 0
    branch1 = 1
    branch2 = 2
    branch3 = 3
    branch4 = 4
    branch5 = 5
    branch6 = 6
    branch7 = 7
    branch8 = 8

@unique
class DecisionScheme(Enum):
    off_chain = 1
    on_chain = 2

class DecisionNode(metaclass=ABCMeta): 
    parent = None
    layerouts:List[str] = None
    is_on_chain: bool = False
    
    def output(self)->List[str]:
        all_layerouts = [] + self.layerouts
        parent: DecisionNode = self.parent
        while parent:
            all_layerouts = parent.layerouts + all_layerouts
            parent = parent.parent
        return all_layerouts 
        
    @abstractmethod
    def check(self, token_info:TokenInfo) -> NodeReturn:
        pass

def generate_node(T:type[DecisionNode], parent:DecisionNode, mode:DecisionScheme):
    node = T()
    node.parent = parent
    node.layerouts = []
    if mode == DecisionScheme.on_chain:
        node.is_on_chain = True
    return node  
