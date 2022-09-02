from flask import Flask
from flask import request
from web3 import Web3
import sys
sys.path.append('.')
from core.token.common.output import token_check_output
from core.utils.source_code import get_sli_c_by_addr
from core.token.check_entry import check_token
from core.common.e import Chain

# from flask_restful import Api, Resource
app = Flask(__name__)

@app.route("/api/getInfo")
def getInfo():
    try:
        chain_id =request.args.get('chainid',type=int)
        assert chain_id in Chain._value2member_map_, f"暂不支持该链：{chain_id}"
        chain = Chain._value2member_map_[chain_id]
        addr = request.args.get('address')
        w3 = Web3()
        assert w3.isAddress(addr),f'{addr}不是一个合法地址'
        
        c = get_sli_c_by_addr(chain, addr)
        check_token(c)
    except Exception as err:
        return f'{err}'
    else:
        return token_check_output.get_output().replace('\n',' <br>')

