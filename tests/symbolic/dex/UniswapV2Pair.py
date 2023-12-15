import sys
sys.path.append('.')
from core.utils.scan_api import get_sli_c
from core.symbolic.state.world_state import WorldState
from core.symbolic.state.machine_state import Call, CallType
from core.symbolic.types import SolBytes
from core.symbolic.vm import ExecVM
from core.symbolic.z3_helper import gene_z3_var_from_elementary

from typing import Mapping

from slither.core.declarations import Contract
import z3

CODE_DIR = "code_dir"
CODE_FILE = "code_file"

pair_address = 1
token0_address = 2
token1_address = 3
caller_address = 100
IUniswapV2Callee = 1000

config = {
    "source":{
        "UniswapV2Pair":{
            "code_dir":"sols/classify/defi/v2-core-master/contracts",
            "code_file":"UniswapV2Pair.sol",
        },
        "ERC20":{
            "code_dir":"sols/classify/@openzeppelin/contracts",
            "code_file":"token/ERC20/ERC20.sol",
        }
    },
    "world_state":{
        pair_address: {
            "source":"UniswapV2Pair",
            "state":{
                "concrete":{
                    "token0":token0_address,
                    "token1":token1_address,
                    "reserve0":10000000,
                    "reserve1":10000000
                },
                "symbolic":{
                    "blockTimestampLast":"uint32"
                }
            }
        },
        token0_address: {
            "source":"ERC20",
            "state":{
                "concrete":{
                    f"_balances.{pair_address}":10000000
                },
                "symbolic":{
                    f"_balances.{caller_address}":"uint256"
                }
            }
        },
        token1_address: {
            "source":"ERC20",
            "state":{
                "symbolic":{
                    f"_balances.{pair_address}":"uint256",
                    f"_balances.{caller_address}":"uint256"
                }
            }
        }
    }
}    

def entry():
    name_to_contract: Mapping[str, Contract] = {}
    for name, source in config["source"].items():
        name_to_contract[name] = get_sli_c(source[CODE_DIR],source[CODE_FILE],name)

    wstate = WorldState()
    for addr, data in config['world_state'].items():
        wstate.set_contract(addr, name_to_contract[data["source"]] )
        if 'state' in data:
            state = data['state']
            if 'concrete' in state:
                for name, val in state['concrete'].items():
                    wstate.set_storage(addr, name, val)
            if 'symbolic' in state:
                for name, elementary_name in state['symbolic'].items():
                    z3_name = wstate.get_key(addr, name)
                    wstate.set_storage(addr, name, gene_z3_var_from_elementary(z3_name, elementary_name))

    wstate.add_constraint(wstate.get_storage(pair_address,"reserve0") <= wstate.get_storage(token0_address, f"_balances.{pair_address}"))
    wstate.add_constraint(wstate.get_storage(pair_address,"reserve1") <= wstate.get_storage(token1_address, f"_balances.{pair_address}"))

    # param1 = z3.BitVec('call0.amount0Out',256)
    # param2 = z3.BitVec('call0.amount1Out',256)
    param1 = z3.Int('call0.amount0Out')
    param2 = z3.Int('call0.amount1Out')
    param3 = IUniswapV2Callee
    param4 = SolBytes()
    call = Call(
        call_type= CallType.Entry,
        target= pair_address,
        function_signature= "swap(uint256,uint256,address,bytes)",
        params= [param1, param2, param3, param4],
        msg_sender= caller_address,
        msg_value= 0,
        tx_origin= caller_address
    ) 

    
    vm = ExecVM()
    vm.start(wstate, call)

def z3_test():
    a=z3.BitVec('a',32)
    b=z3.BitVec('b',16)
    s = z3.Solver()
    s.add(a*b==1000)
    if s.check():
        model = s.model()
    print(model)

if __name__ == "__main__":
    entry()
    # z3_test()
