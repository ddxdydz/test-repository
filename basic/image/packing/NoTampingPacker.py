import numpy as np

from basic.image.packing.ABC_Packer import Packer


class NoTampingPacker(Packer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pack_array(self, array: np.ndarray) -> bytes:
        self._validate_array(array)
        packed_array = array.flatten().tobytes()
        header = self._pack_shape(array.shape)
        return header + packed_array

    def unpack_array(self, data: bytes) -> np.ndarray:
        shape, packed_array = self._unpack_shape_header(data)
        unpacked_array = np.frombuffer(packed_array, dtype=np.uint8).reshape(shape)
        self._validate_array(unpacked_array)
        return unpacked_array
