from mythril.laser.ethereum.state.global_state import GlobalState

def get_first_annotation(global_state:GlobalState, T)->any:
    for annotation in global_state.annotations:
        if isinstance(annotation, T):
            return annotation # 只返回第一个，约定只有一个该对象
    return None
