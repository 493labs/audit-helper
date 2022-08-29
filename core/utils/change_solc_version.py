import subprocess
import sys
from typing import List

def change_solc_version(sol_path:str):
    # 获取已有的solc版本
    res = subprocess.check_output(['solc-select', 'versions'])
    versions = []
    cur_version = ''
    for item in res.splitlines():
        item = str(item,encoding='utf-8')
        if 'current' in item:
            cur_version = item.split()[0]
            versions.append(cur_version)
        else:
            versions.append(item)
    print(f'当前solc版本：{cur_version}')

    # 获取sol文件需要的版本
    obj_version = ''
    with open(sol_path,'r',encoding='utf-8') as fp:
        for line in fp.readlines():
            line = line.strip()
            if line.startswith('pragma'):
                line = line[6:].strip()
                if line.startswith('solidity'):
                    line = line[8:-1].strip()
                    break
        # 1. pragma solidity 0.6.9;
        # 2. pragma solidity ^0.6.9;
        # 3. pragma solidity >=0.6.9 <=0.6.9;
        # 只考虑前面2中情况
        if line.startswith('0'):
            obj_version = line
        elif line.startswith('^'):
            def digit(s:str)->List[int]:
                ss = s.split('.')
                assert len(ss)==3, f'编译器版本格式有误：{s}'
                return [int(si) for si in ss]

            versions.insert(0,cur_version)
            demands = digit(line[1:])
            for item in versions:
                supplys = digit(item)
                if supplys[0]==demands[0] and supplys[1]==demands[1] and supplys[2]>=demands[2]:
                    obj_version = item
                    break
        else:
            print(f'为考虑这种模式：{line}，可能需要人工设置')
            return
    print(f'需要solc版本：{obj_version}')

    # 切换版本
    if  obj_version not in versions or obj_version == '':
        print("未找到合适的solidity版本，需要先安装，")
        sys.exit()
    elif obj_version != cur_version:
        subprocess.call(f'solc-select use {obj_version}')
