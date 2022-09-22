from configparser import ConfigParser
import os
import sys
sys.path.append('.')
from core.common.e import Chain
from core.utils.source_code import get_sli_c_by_addr,download
from core.decision_tree.token.frame import make_decision

DOWNLOAD = 'download'

def handle(config: ConfigParser):
    chain_id = config.getint(DOWNLOAD,'chain_id')
    assert chain_id in Chain._value2member_map_, f"暂不支持该链：{chain_id}"
    chain = Chain._value2member_map_[chain_id]
    
    token_address = config.get(DOWNLOAD,'token_address')

    if config.getboolean(DOWNLOAD, 'with_token_check'):
        c = get_sli_c_by_addr(chain, token_address)
        layerouts = make_decision(on_chain=True, chain=chain, address=token_address, c=c)
        for layerout in layerouts:
            print(layerout)
    else:
        download(chain, token_address)

if __name__ == "__main__":
    config = ConfigParser()
    config.read(os.path.dirname(__file__) + '/token.ini', 'utf-8')      
    handle(config)
    
