from typing import List
from distutils import core

from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import ERC20_E_view, ERC721_E_view, TokenInfo, ERC20_E_Require, ERC721_E_Require

from slither.core.declarations import Function
from slither.core.cfg.node import NodeType

class SearchIfAndLoop(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:

        def have_loop(f: Function)->bool:
            for node in f.all_nodes():
                #if node.type in [NodeType.IF, NodeType.IFLOOP]:
                if node.type in [NodeType.IFLOOP]:
                    return True
            return False

        transfer_fs:List[Function] = []
        if token_info.is_erc20:
            transfer_fs.append(token_info.get_f(ERC20_E_Require.transfer))
            transfer_fs.append(token_info.get_f(ERC20_E_Require.transferFrom))
        if token_info.is_erc721:
            transfer_fs.append(token_info.get_f(ERC721_E_Require.transferFrom))
            transfer_fs.append(token_info.get_f(ERC721_E_Require.safeTransferFrom))
            transfer_fs.append(token_info.get_f(ERC721_E_Require.safeTransferFrom2))

        for f in transfer_fs:
            if have_loop(f):
                self.add_warn(f'{f.name} 存在if分支或者循环，需要注意gas消耗问题')
        
        if len(self.layerouts) == 0:
            self.add_info('转账方法中不存在if分支和循环')
            
        return NodeReturn.branch0