import os

def true() -> bool:
    return True

def false() -> bool:
    return False

def env_is_divisible_by(env_var: str, by: str) -> bool:
    value = int(os.environ[env_var])
    by_int = int(by)
    return value % by_int == 0
