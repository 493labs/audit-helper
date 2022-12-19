from .nodes.classify import ClassifyNode
from .nodes.fund_verify import FundVerifyNode

decision_tree = {
    ClassifyNode: [FundVerifyNode]
}