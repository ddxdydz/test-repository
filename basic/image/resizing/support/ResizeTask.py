from typing import Tuple, Optional


class ResizeTask:
    """Класс для описания задачи изменения размера"""

    def __init__(self,
                 scale: Optional[float] = None,
                 size: Optional[Tuple[int, int]] = None,
                 max_size: Optional[Tuple[int, int]] = None,
                 width: Optional[int] = None,
                 height: Optional[int] = None):
        """
        Инициализация задачи изменения размера

        Args:
            size: Точный размер (width, height)
            scale: Масштабный коэффициент
            max_size: Максимальный размер (width, height) - сохраняет пропорции
            width: Фиксированная ширина (высота вычисляется автоматически)
            height: Фиксированная высота (ширина вычисляется автоматически)
        """
        self.size = size
        self.scale = scale
        self.max_size = max_size
        self.width = width
        self.height = height

        # Проверяем, что задан только один способ изменения размера
        params = [size, scale, max_size, width, height]
        specified_params = [p for p in params if p is not None]
        if len(specified_params) != 1:
            raise ValueError("Должен быть указан только один параметр изменения размера")

    def calculate_size(self, original_size: Tuple[int, int]) -> Tuple[int, int]:
        """Вычисляет конечный размер на основе задачи и исходного размера"""
        original_width, original_height = original_size

        if self.size:
            return self.size

        elif self.scale:
            new_width = int(original_width * self.scale)
            new_height = int(original_height * self.scale)
            return max(1, new_width), max(1, new_height)

        elif self.max_size:
            max_width, max_height = self.max_size
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            return max(1, new_width), max(1, new_height)

        elif self.width:
            ratio = self.width / original_width
            new_height = int(original_height * ratio)
            return self.width, max(1, new_height)

        elif self.height:
            ratio = self.height / original_height
            new_width = int(original_width * ratio)
            return max(1, new_width), self.height

        else:
            return original_size

    def __str__(self) -> str:
        if self.size:
            return f"ResizeTask(size={self.size})"
        elif self.scale:
            return f"ResizeTask(scale={self.scale})"
        elif self.max_size:
            return f"ResizeTask(max_size={self.max_size})"
        elif self.width:
            return f"ResizeTask(width={self.width})"
        elif self.height:
            return f"ResizeTask(height={self.height})"
        else:
            return "ResizeTask(no_change)"
