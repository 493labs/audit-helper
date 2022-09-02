from configparser import ConfigParser
import os
import sys
sys.path.append('.')
from core.common.e import Chain
from core.utils.source_code import get_sli_c_by_token_info,download
from core.token.check_entry import check_token
from core.token.common.output import token_check_output

DOWNLOAD = 'download'

def handle(config: ConfigParser):
    chain_id = config.getint(DOWNLOAD,'chain_id')
    assert chain_id in Chain._value2member_map_, f"暂不支持该链：{chain_id}"
    chain = Chain._value2member_map_[chain_id]
    
    token_address = config.get(DOWNLOAD,'token_address')
    token_name = config.get(DOWNLOAD,'token_name')
    token_type = config.get(DOWNLOAD, 'token_type')

    if config.getboolean(DOWNLOAD, 'with_token_check'):
        c = get_sli_c_by_token_info(chain, token_address,token_type,token_name)
        check_token(c)
    else:
        download(chain, token_address,token_type,token_name)

if __name__ == "__main__":
    try:
        config = ConfigParser()
        config.read(os.path.dirname(__file__) + '/token.ini', 'utf-8')      
        handle(config) 
    except Exception as err:
        print(err.with_traceback())
    else:
        print(token_check_output.get_output())
    
