# audit-helper

## 当前已实现：

1. 输出合约的调用关系图（所有的外部调用、内部调用和两者之和，以及针对单个方法的调用关系）

## 正常运行依赖组件
1. python版本>=`3.10.1`（未在其它版本测过）
2. solidity静态扫描工具slither， `pip install slither`
3. 与目标sol文件匹配的solidity编译器，可以使用 `solc-select` 进行管理， `pip install solc-select`

## 运行
在项目根目录运行 `python main.py`  
程序运行基于配置文件 `config.ini` ，位于 `main.py` 同级目录，内容如下  
```ini
[target]
contract_root_path = contracts\teleport ;若有openzeppelin依赖则将@openzeppelin目录放于此处
contract_path = core\packet\Packet.sol
contract_name = Packet
function_names = sendPacket,sendMultiPacket,executePacket,acknowledgePacket,recvPacket
analyze_global = True ;是否输出全局调用关系图，位于contract_root_path下的output
analyze_function = False ；;是否输出特定方法的调用关系图，位于contract_root_path下的output
```

