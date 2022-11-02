from ...base_node import TokenDecisionNode, NodeReturn
from ...token_info import TokenInfo

class MetaTransaction(TokenDecisionNode):

    def token_check(self, token_info: TokenInfo) -> NodeReturn:
        fs_have_meta_tr = []
        for f in token_info.c.functions_entry_points:
            ecrecover_calls = [solidity_call for solidity_call in f.all_solidity_calls() if 'ecrecover' in solidity_call.name]
            ECDSA_recover_calls = [library_call for library_call in f.all_library_calls() if library_call[0].name == 'ECDSA' and library_call[1].name == 'recover']
            if ecrecover_calls or ECDSA_recover_calls:
                fs_have_meta_tr.append(f)
                
        if fs_have_meta_tr:
            fnames = ','.join([f.full_name for f in fs_have_meta_tr])
            self.add_focus(f'{fnames} 中存在元交易，注意检查 nonce 的使用')
        else:
            self.add_info('未发现存在元交易的情况')
        return NodeReturn.branch0