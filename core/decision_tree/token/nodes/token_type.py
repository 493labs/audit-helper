from core.token.token_identify import identify_token
from core.token.common.e import TokenType
from ..common.base_node import DecisionNode, NodeReturn
from ..common.standard import TokenInfo


class TokenTypeNode(DecisionNode):

    def check(self, token_info: TokenInfo) -> NodeReturn:
        token_type = identify_token(token_info.c)
        self.layerouts.append(f'代币类型为{token_type.name}')
        if token_type == TokenType.ERC20:
            return NodeReturn.branch0
        elif token_type == TokenType.ERC721:
            self.layerouts.append(f'暂未对erc721进行分析')
            return NodeReturn.reach_leaf
        else:
            self.layerouts.append(f'未知的代币类型，无法进一步分析')
            return NodeReturn.reach_leaf
        
