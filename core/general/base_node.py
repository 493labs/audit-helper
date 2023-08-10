from abc import abstractmethod
from typing import List
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo
from colorama import Fore

def get_risk_level(node: DecisionNode) -> str:
    node_name = node.__class__.__name__
    risk_level = 'unknown'
    if node_name in ['TokenTypeNode','StateNode','CloseCheckNode']:
        risk_level = 'pre work(H1 H3 H10 H11)'
    elif node_name == 'UnlimitMint':
        risk_level = 'H2 M2'
    return f'[{risk_level}] '

def rank_layerouts(layerouts: List[str]) -> List[str]:
    pre_work_layerouts = []
    other_layerouts = []
    for layerout in layerouts:
        if layerout[5:].startswith('[pre work'):
            pre_work_layerouts.append(layerout)
        else:
            other_layerouts.append(layerout)
    return pre_work_layerouts + sorted(other_layerouts)
    
class ContractDecisionNode(DecisionNode):

    def add_warns(self, warns:List[str]):
        self.layerouts.extend([Fore.RED + get_risk_level(self) + Fore.RED + warn for warn in warns])

    def add_warn(self, warn:str):
        self.layerouts.append(Fore.RED + get_risk_level(self) + warn)

    def add_focuss(self, focus_infos:List[str]):
        self.layerouts.extend([Fore.YELLOW + get_risk_level(self) + focus_info for focus_info in focus_infos])

    def add_focus(self, focus_info:str):
        self.layerouts.append(Fore.YELLOW + get_risk_level(self) + focus_info)

    def add_infos(self, infos:List[str]):
        self.layerouts.extend([Fore.GREEN + get_risk_level(self) + info for info in infos])

    def add_info(self, info:str):
        self.layerouts.append(Fore.GREEN + get_risk_level(self) + info)
    
    def check(self, contract_info: ContractInfo) -> NodeReturn:
        return self.contract_check(contract_info)

    @abstractmethod
    def contract_check(self, contract_info:ContractInfo) -> NodeReturn:
        pass

