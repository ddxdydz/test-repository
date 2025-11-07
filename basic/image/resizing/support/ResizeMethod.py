from enum import Enum


class ResizeMethod(Enum):
    """Перечисление методов изменения размера"""
    NEAREST = "nearest"
    BILINEAR = "bilinear"
    BICUBIC = "bicubic"
    LANCZOS = "lanczos"
    AREA = "area"
