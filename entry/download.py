import json
import os
import sys
sys.path.append('.')
from core.utils.url import Chain
from core.utils.scan_api import SourceCode

PROJECTNAME = 'project-name'
CHAINID = 'chain-id'
CONTENT = 'content'

JSONFILE = 'download.json'
ROOTPATH = 'sols/project'

if __name__ == "__main__":
    with open(os.path.dirname(__file__)+f'/{JSONFILE}','r') as fp:
        download_config = json.load(fp)

    chain_id = download_config[CHAINID]
    assert chain_id in Chain._value2member_map_, f"暂不支持该链：{chain_id}"
    chain = Chain._value2member_map_[chain_id]

    project_name = download_config[PROJECTNAME]
    assert project_name
    code_dir = f'{ROOTPATH}/{project_name}'

    json_file = f'{code_dir}/{JSONFILE}'
    if not os.path.exists(json_file):
        content = download_config[CONTENT]
        for address in content.values():
            source_code = SourceCode(chain,address,code_dir)
            source_code.download(gene_conf_file=False)
        with open(json_file,'w') as fp:
            json.dump(download_config, json_file)
