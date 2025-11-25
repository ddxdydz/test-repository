from time import time
from typing import Optional


def time_ms(value: Optional[float] = None) -> int:
    """value in seconds to value in milliseconds"""
    if value is None:
        value = time()
    return int(value * 1000)
