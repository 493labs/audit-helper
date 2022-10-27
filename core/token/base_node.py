from abc import abstractmethod
from core.frame.base_node import DecisionNode, NodeReturn
from core.frame.contract_info import ContractInfo
from .token_info import TokenInfo

class TokenDecisionNode(DecisionNode):
    
    def check(self, contract_info: ContractInfo) -> NodeReturn:
        return self.token_check(contract_info)

    @abstractmethod
    def token_check(self, token_info:TokenInfo) -> NodeReturn:
        pass

