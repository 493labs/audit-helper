from configparser import ConfigParser
import os
import sys
sys.path.append('.')
from core.utils.url import Chain
from core.utils.scan_api import get_sli_c_by_addr,download
from core.token.check_frame import token_decision
from core.token.base_node import rank_layerouts

DOWNLOAD = 'download'

def handle(config: ConfigParser):
    chain_id = config.getint(DOWNLOAD,'chain_id')
    assert chain_id in Chain._value2member_map_, f"暂不支持该链：{chain_id}"
    chain = Chain._value2member_map_[chain_id]
    
    token_address = config.get(DOWNLOAD,'token_address')

    if config.getboolean(DOWNLOAD, 'with_token_check'):
        # 入口contract
        c = get_sli_c_by_addr(chain, token_address)
        layerouts = token_decision(on_chain=True, chain=chain, address=token_address, c=c)
        for layerout in rank_layerouts(layerouts):
            print(layerout)
    else:
        download(chain, token_address)

if __name__ == "__main__":
    config = ConfigParser()
    config.read(os.path.dirname(__file__) + '/token.ini', 'utf-8')      
    handle(config)
    
