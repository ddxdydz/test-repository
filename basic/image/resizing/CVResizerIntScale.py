from typing import Tuple, Optional

from basic.image.resizing.ABC_ImageResizer import ResizeMethod
from basic.image.resizing.CVResizer import CVResizer


class CVResizerIntScale(CVResizer):
    """Версия с использованием 1 < scale_percent: int <= 100 вместо scale:float >= 0"""
    def __init__(self, scale_percent: int = 60, method: ResizeMethod | int = ResizeMethod.BICUBIC,
                 original_size: tuple[int, int] | None = None):
        self.scale_percent = self._get_validated_scale_percent(scale_percent)
        super().__init__(self.scale_percent / 100, method, original_size)

    @staticmethod
    def _get_validated_scale_percent(scale_percent: int) -> int:
        if scale_percent < 1 or scale_percent > 100:
            raise ValueError(f"Error in ImageResizer: Scale percent must be between 1 and 100")
        return scale_percent

    def set_scale_percent(self, scale_percent: int) -> None:
        """Установить новый коэффициент масштабирования в процентах"""
        self.scale_percent = self._get_validated_scale_percent(scale_percent)
        self.set_scale(self.scale_percent / 100)

    def get_parameters_int(self) -> Tuple[int, int, int, int]:
        """Получить текущие параметры масштабирования"""
        width, height = self.original_size
        return width, height, self.scale_percent, self.method.get_index()

    def set_parameters_int(self, width: int, height: int, scale_percent: int, method: int) -> None:
        """Установить параметры масштабирования"""
        self.set_method(method)
        self.set_scale_percent(scale_percent)
        self.set_original_size((width, height))
