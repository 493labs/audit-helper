from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import TokenInfo

from slither.core.declarations import Function

def random_exp(f: Function):
    for node in f.all_nodes():
        if node.solidity_calls:
            count = 0
            for sol_call in node.solidity_calls:
                if sol_call.name == "abi.encodePacked()" or sol_call.name == "keccak256(bytes)":
                    count += 1
            # 包含abi.encodePacked和keccak256，并且参数有solidity variable
            if count == 2 and len(node.solidity_variables_read) > 0:
                return True
    return False      


def check_sender(f: Function):
    for node in f.all_nodes():
        # 检查 require(msg.sender == tx.origin)
        if len(node.solidity_calls) == 1 and node.solidity_calls[0].name == "require(bool,string)":
            count = 0
            for v in node.variables_read:
                if v.name == "msg.sender" or v.name == "tx.origin":
                    count += 1
            if count == 2:
                return True
    return False


class RandomCheck(TokenDecisionNode):
    
    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        layerouts = []
        if token_info.is_erc721:
            for f in token_info.c.functions:
                if random_exp(f) and not check_sender(f):
                    layerouts.append(f'{f.full_name} 存在未正确使用随机数的风险')
        
        if len(layerouts) == 0:
            self.add_info(f'未发现随机数风险的方法')
        else:
            self.add_warns(layerouts)
        return NodeReturn.branch0