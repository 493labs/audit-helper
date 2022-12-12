from abc import abstractmethod
from typing import List
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo
from .token_info import TokenInfo
from colorama import Fore

def get_risk_level(node: DecisionNode) -> str:
    node_name = node.__class__.__name__
    risk_level = 'unknown'
    if node_name in ['TokenTypeNode','StateNode','CloseCheckNode']:
        risk_level = 'pre work(H3 H8 H10 H11)'
    elif node_name == 'RequiredFuncNode':
        risk_level = 'H5'
    elif node_name == 'SearchIfAndLoop':
        risk_level = 'O1'
    elif node_name == 'TransferOtherNode':
        risk_level = 'H4'
    elif node_name == 'CheatState':
        risk_level = 'H6'
    elif node_name == 'ArbitraryMint':
        risk_level = 'H9'
    elif node_name == 'CalculationOrder':
        risk_level = 'H13 M11'
    elif node_name == 'ExternalCallNode':
        risk_level = 'other'
    elif node_name == 'BackDoorNode':
        risk_level = 'H17'
    elif node_name == 'NotZeroAddress':
        risk_level = 'M12'
    elif node_name == 'MetaTransaction':
        risk_level = 'H15'
    elif node_name == 'OverflowNode':
        risk_level = 'H12'
    elif node_name == 'FakeRecharge':
        risk_level = 'H7'
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
    
class TokenDecisionNode(DecisionNode):

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
        return self.token_check(contract_info)

    @abstractmethod
    def token_check(self, token_info:TokenInfo) -> NodeReturn:
        pass

