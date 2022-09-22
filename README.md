# audit-helper

## 依赖
1. python版本>=`3.10.1`（未在其它版本测过）
2. 安装依赖 `pip install -r requirements.txt`, 可以选择性的安装虚拟环境, 使用的时候建议使用虚拟环境

## 配置
```ini
; 文件位于`conf/key.ini`
[key]
infura_key = xxxxxxxxxx
```

```ini
; 文件位于`entry/token.ini`
[download]
; 目前支持ETH、BSC、XAVA-C链，分别为1、56、43114
chain_id = 56 
token_address = 0x477bc8d23c634c154061869478bce96be6045d12
; 下载完成后是否进行`token`的各项检查 True or False
with_token_check = True
```

## 运行
### token检查
在项目根目录运行 `python ./entry/token_entry.py` 
