from basic.network.tools.time_ms import time_ms


class CooldownChecker:
    def __init__(self, _cooldown_ms: int):
        if _cooldown_ms < 1:
            raise ValueError(f"Cooldown must be positive, got {_cooldown_ms}")
        self._cooldown_ms = _cooldown_ms
        self._last_time_ms = 0

    def check_cooldown(self) -> bool:
        current_time_ms = time_ms()
        if current_time_ms - self._last_time_ms < self._cooldown_ms:
            return False
        self._last_time_ms = current_time_ms
        return True
