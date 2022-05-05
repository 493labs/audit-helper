import subprocess

def change_solc_version(sol_path:str):
    # 获取已有的solc版本
    res = subprocess.check_output('solc-select versions')
    versions = []
    cur_version = ''
    for item in res.splitlines():
        item = str(item,encoding='utf-8')
        if 'current' in item:
            cur_version = item.split()[0]
            versions.append(cur_version)
        else:
            versions.append(item)

    # 获取sol文件需要的版本
    obj_version = ''
    with open(sol_path,'r') as fp:
        for line in fp.readlines():
            line = line.strip()
            if line.startswith('pragma'):
                line = line[6:].strip()
                if line.startswith('solidity'):
                    line = line[8:-1].strip()
                    break
        # 只考虑 = 和 ^ 的情况
        prefix = line[0]
        v = line[1:]
        if prefix == '=':
            if v in versions:
                obj_version = v
        if prefix == '^':
            for item in versions:
                if item.startswith(v[:3]) and item >= v:
                    obj_version = item
                    break
    # 切换版本
    if obj_version == '':
        print('未找到合适的solidity版本')
    elif obj_version != cur_version:
        subprocess.call(f'solc-select use {obj_version}')