from slither.core.declarations import Function

def get_function_signature(f:Function) -> str:
    name, parameters, _ = f.signature
    return name + "(" + ",".join(parameters) + ")"