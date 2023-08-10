import time
from core.utils.scan_api import get_contract_creation
from core.utils.node_api import ReadSlot

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import TokenInfo


class ReplayAttack(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        # etherscan api 频率限制 5s 一次请求
        time.sleep(6)
        contractcreation_txhash = get_contract_creation(token_info.chain, token_info.address)[1]
        read_slot = ReadSlot(token_info.chain)
        tx_sig = read_slot.read_sig_by_txhash(contractcreation_txhash)
        # 如果v值为27或者28则存在重放风险
        if tx_sig[2] == 27 or tx_sig[2] == 28:
            self.add_warn("contract_creation 交易未遵守EIP155/EIP2817, 存在多链部署，重放风险")
        else:
            self.add_info('contract_creation 交易遵守EIP155/EIP2817, 不存在多链部署，重放风险')
        
        return NodeReturn.branch0