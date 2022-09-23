from abc import ABCMeta, abstractmethod
from enum import Enum, unique
from typing import List
from .token import TokenInfo
from colorama import Fore

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

class DecisionNode(metaclass=ABCMeta): 
    parent = None
    layerouts:List[str] = None
    on_chain: bool = False

    def add_warns(self, warns:List[str]):
        self.layerouts.extend([Fore.RED + warn for warn in warns])

    def add_warn(self, warn:str):
        self.layerouts.append(Fore.RED + warn)

    def add_infos(self, infos:List[str]):
        self.layerouts.extend([Fore.GREEN + info for info in infos])

    def add_info(self, info:str):
        self.layerouts.append(Fore.GREEN + info)
    
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

def generate_node(T:type[DecisionNode], parent:DecisionNode, on_chain:bool):
    node = T()
    node.parent = parent
    node.layerouts = []
    node.on_chain = on_chain
    return node  

