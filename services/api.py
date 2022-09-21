from flask import Flask
from flask import request
from web3 import Web3
import sys
sys.path.append('.')
from core.common.e import Chain
from core.decision_tree.token.frame import make_decision
from core.decision_tree.token.common.base_node import DecisionScheme


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
        
        layerouts = make_decision(DecisionScheme.on_chain, chain, addr)
    except Exception as err:
        return f'{err}'
    else:
        return layerouts

