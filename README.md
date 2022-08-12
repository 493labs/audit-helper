# audit-helper

## 模块
1. token检查，包括 `erc20` 和 `erc721`
2. 合约分析
3. 工具

## 依赖
1. python版本>=`3.10.1`（未在其它版本测过）
2.安装依赖 `pip install -r requirements.txt`, 可以选择性的安装虚拟环境, 使用的时候建议使用虚拟环境

## erc20检查
1. 转账与授权逻辑检查
2. 拓展方法（burn、increaseAllowance、decreaseAllowance）检查
3. 对balances、allowance的写入操作只通过标准方法
4. 溢出检查
5. 外部调用检查
6. 假充值检查

## erc721检查
1. 封闭性检查
2. 标准方法读写检查
3. 写重要状态的方法外部调用检查

## 合约分析
1. 输出合约的调用关系图（所有的外部调用、内部调用，以及针对单个方法的调用关系）,状态读写图
2. 危险的外部调用检查（外部调用的地址基于输入的（可能在其它方法中）参数）

## 工具
1. 自动下载链上已验证代码到本地
2. 读取链上的`mapping`对应的`slot`，需要配置`infura_key`
3. 自动切换`solc`版本
```ini
; 文件位于`conf/key.ini`
[key]
infura_key = xxxxxxxxxx
```


## 运行
### token检查
在项目根目录运行 `python ./entry/token_entry.py`  
程序运行基于配置文件 `token.ini` ，位于 `token_entry.py` 同级目录，内容如下  
```ini
[download]
; 目前支持ETH、BSC、XAVA-C链，分别为1、56、43114
chain_id = 56 
token_address = 0x477bc8d23c634c154061869478bce96be6045d12
; 包括erc20、erc721、other，分别为1、2、99。用于区分下载目录
token_type = 1
token_name = SFUND
; 下载完成后是否进行`token`的各项检查
with_token_check = True
```

### audit检查
在项目根目录运行 `python ./entry/audit_entry.py`  
程序运行基于配置文件 `audit.ini` ，位于 `audit_entry.py` 同级目录，内容如下  
```ini
[audit-helper]
; 每个段都有一个`open`属性，用于控制是否执行此模块
; 若有`openzeppelin`依赖则将`@openzeppelin`目录放于此处
root_path = contracts\teleport
contract_path = core\packet\Packet.sol
contract_name = Packet

; 是否分析调用关系图
with_call_graph = True
function_names = sendPacket,sendMultiPacket,executePacket,acknowledgePacket,recvPacket
; 是否输出全局调用关系图，位于`root_path`下的`output`
global_call_graph = True
; 是否输出特定方法的调用关系图，位于`root_path`下的`output`
function_call_graph = True
; 是否输出合约的状态变量以及方法对其读写情况的关系图
write_read_graph = False

; 是否分析危险的外部调用
with_external_call_check = False
```

