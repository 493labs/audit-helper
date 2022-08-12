from configparser import ConfigParser
import os
from slither import Slither
import sys
sys.path.append('.')
from core.common.e import Chain, TokenType
from core.utils.source_code import SourceCode
from core.utils.change_solc_version import change_solc_version
from core.token.check_entry import check_token

DOWNLOAD = 'download'

def _check_token(code_path:str):
    check_conf_path = code_path + '/check.ini'
    assert os.path.exists(check_conf_path), '请先下载代码'
    token_conf = ConfigParser()
    token_conf.read(check_conf_path, 'utf-8')
    os.chdir(code_path)
    contract_path = token_conf.get('info', 'contract_path')
    change_solc_version(contract_path)
    sli = Slither(contract_path)
    for c in sli.contracts_derived:
        if c.kind!="contract":
            continue
        check_token(c)

def download(config: ConfigParser):
    chain_id = config.getint(DOWNLOAD,'chain_id')
    for e in Chain._member_map_.values():
        if chain_id == e.value:
            chain = e
            break
    assert 'chain' in locals(), "暂不支持该链：" + str(chain_id)
    
    token_address = config.get(DOWNLOAD,'token_address')
    token_name = config.get(DOWNLOAD,'token_name')
    token_type_id = config.getint(DOWNLOAD, 'token_type')
    for e in TokenType._member_map_.values():
        if token_type_id == e.value:
            token_type = e
            break
    if 'token_type' not in locals():
        token_type = TokenType.OTHER

    source_code = SourceCode(chain, token_address, token_type, token_name)
    source_code.download()
    if config.getboolean(DOWNLOAD, 'with_token_check'):        
        _check_token(source_code.get_code_path())

if __name__ == "__main__":
    config = ConfigParser()
    config.read(os.path.dirname(__file__) + '/token.ini', 'utf-8')   
    download(config) 
    
