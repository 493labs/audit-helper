# audit-helper

# 依赖
1. python版本>=`3.10.1`（未在其它版本测过）
2. 安装依赖 `pip install -r requirements.txt`, 可以选择性的安装虚拟环境, 使用的时候建议使用虚拟环境

# token下载与分析
## 配置
文件位于`conf/key.ini`
```ini
[key]
infura_key = xxxxxxxxxx
```
文件位于`entry/token.ini`
```ini
[download]
; 目前支持的链：
; ETH   1
; BSC   56
; XAVA-C链  43114
; Polygon   137
; ArbitrumOne   42161
; Goerli    5
; Mantle    5000
; Optimistic    10
chain_id = 56 
token_address = 0x477bc8d23c634c154061869478bce96be6045d12
; 下载完成后是否进行`token`的各项检查 True or False
with_token_check = True
```
## 运行
在项目根目录运行 `python ./entry/token_entry.py` 

# 非token项目代码下载
## 配置
文件位于`entry/download.json`
```json
{
    "project-name":"some name",
    "chain-id":1,
    "content":{
        "contract1":"address1",
        "contract2":"address2",
        "contract3":"address3"
    }
}
```
## 运行
在项目根目录运行 `python ./entry/download.py`