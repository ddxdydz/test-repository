from time import time
from typing import List, Tuple

import numpy as np

from basic.image.packing.ABC_Packer import Packer


class PackerBenchmark:
    BITS_PER_VALUE_LIST = list(range(1, 9))
    TEST_CORRECTNESS_DATA_SHAPES = [(100, 100, 1), (200, 250, 2), (232, 201, 3)]
    TEST_SPEED_DATA_SHAPES = [(2000, 2000, 1), (2000, 2000, 2), (2000, 2000, 3),
                              (200, 200, 1), (200, 200, 2), (200, 200, 3)]
    TEST_SPEED_DATA_SHAPE_REGULAR = (1200, 800, 1)

    def __init__(self):
        self._test_data_cache = {}

    def _generate_test_data(self, bits_per_value: int, shape: Tuple[int, int, int]) -> np.ndarray:
        """Генерирует тестовые данные для заданной битности и формы"""
        cache_key = (bits_per_value, shape)
        if cache_key not in self._test_data_cache:
            max_value = (1 << bits_per_value) - 1
            data = np.random.randint(0, max_value + 1, shape, dtype=np.uint8)
            self._test_data_cache[cache_key] = data
        return self._test_data_cache[cache_key]

    def _test_correctness(self, packer: Packer, bits_per_value: int,
                          test_shapes: List[Tuple[int, int, int]] = None) -> bool:
        """
        Тестирует корректность упаковки/распаковки для различных форм данных

        Returns:
            bool: True если все тесты пройдены
        """
        if test_shapes is None:
            test_shapes = self.TEST_CORRECTNESS_DATA_SHAPES

        for shape in test_shapes:
            original_data = self._generate_test_data(bits_per_value, shape)
            try:
                # Тестируем упаковку и распаковку
                packed_data = packer.pack_array(original_data)
                unpacked_data = packer.unpack_array(packed_data)
                # Проверяем, что данные совпадают
                if not np.array_equal(original_data, unpacked_data):
                    print(f"Correctness test failed for {packer.__class__.__name__}, "
                          f"bits={bits_per_value}, shape={shape}")
                    print(f"Original shape: {original_data.shape}, "
                          f"Unpacked shape: {unpacked_data.shape}")
                    return False
            except Exception as e:
                print(f"Error in correctness test for {packer.__class__.__name__}: {e}")
                return False
        return True

    def _test_performance_packing(self, packer: Packer, bits_per_value: int,
                                  shape: Tuple[int, int, int], iterations: int = 100) -> float:
        test_data = self._generate_test_data(bits_per_value, shape)

        # Тестируем упаковку
        pack_times = []
        for _ in range(iterations):
            start_time = time()
            _ = packer.pack_array(test_data)
            pack_times.append(time() - start_time)

        return float(np.mean(pack_times))

    def _test_performance_unpacking(self, packer: Packer, bits_per_value: int,
                                    shape: Tuple[int, int, int], iterations: int = 100) -> float:

        test_data = self._generate_test_data(bits_per_value, shape)
        packed_data = packer.pack_array(test_data)

        # Тестируем распаковку
        unpack_times = []
        if packed_data is not None:
            for _ in range(iterations):
                start_time = time()
                _ = packer.unpack_array(packed_data)
                unpack_times.append(time() - start_time)

        return float(np.mean(unpack_times))

    def _test_compress(self, packer: Packer, bits_per_value: int,
                       shape: Tuple[int, int, int]) -> float:

        test_data = self._generate_test_data(bits_per_value, shape)
        packed_data = packer.pack_array(test_data)
        return len(packed_data) / len(test_data.tobytes())

    def test(self, packers: List[Packer], iterations=10):
        data_for_speed_test = self.TEST_SPEED_DATA_SHAPE_REGULAR
        print(np.prod(data_for_speed_test), data_for_speed_test)
        print(str().rjust(20), *[str(bpv).rjust(10, ' ') for bpv in self.BITS_PER_VALUE_LIST],
              "avg".rjust(10, ' '), sep="\t")

        for packer in packers:
            # Correctness
            print(packer.name.rjust(20), end="\t")
            for bits_per_value in self.BITS_PER_VALUE_LIST:
                packer.set_bits_per_value(bits_per_value)
                if not self._test_correctness(packer, bits_per_value):
                    print(packer, bits_per_value, "_test_correctness is failed")
                    return
                print("yes".rjust(10), end="\t")
            print()

            # Packing speed
            print(f"packing(sec)".rjust(20), end="\t")
            avg_pack_times = []
            for bits_per_value in self.BITS_PER_VALUE_LIST:
                packer.set_bits_per_value(bits_per_value)
                avg_pack_time = self._test_performance_packing(
                    packer, bits_per_value, shape=data_for_speed_test, iterations=iterations)
                print(f"{avg_pack_time:.6f}".rjust(10), end="\t")
                avg_pack_times.append(avg_pack_time)
            print(f"{float(np.mean(avg_pack_times)):.6f}")

            # Unpacking speed
            print(f"unpacking(sec)".rjust(20), end="\t")
            avg_unpack_times = []
            for bits_per_value in self.BITS_PER_VALUE_LIST:
                packer.set_bits_per_value(bits_per_value)
                avg_unpack_time = self._test_performance_unpacking(
                    packer, bits_per_value, shape=data_for_speed_test, iterations=iterations)
                print(f"{avg_unpack_time:.6f}".rjust(10), end="\t")
                avg_unpack_times.append(avg_unpack_time)
            print(f"{float(np.mean(avg_unpack_times)):.6f}")

            # Compress
            print(f"compress_ratio".rjust(20), end="\t")
            for bits_per_value in PackerBenchmark.BITS_PER_VALUE_LIST:
                packer.set_bits_per_value(bits_per_value)
                ratio = self._test_compress(packer, bits_per_value, shape=data_for_speed_test)
                print(f"{ratio:.6f}".rjust(10), end="\t")
            print()


if __name__ == "__main__":
    from basic.image.packing.ShiftPacker import ShiftPacker
    from basic.image.packing.NumbaPacker import NumbaPacker
    from basic.image.packing.CombPacker import CombPacker

    tester = PackerBenchmark()
    tester.test([CombPacker(), ShiftPacker(), NumbaPacker()], iterations=200)

"""
960000 (1200, 800, 1)
                    	         1	         2	         3	         4	         5	         6	         7	         8	       avg
          CombPacker	       yes	       yes	       yes	       yes	       yes	       yes	       yes	       yes	
        packing(sec)	  0.000487	  0.002264	  0.004303	  0.002256	  0.004835	  0.006315	  0.009209	  0.001467	0.003892
      unpacking(sec)	  0.000332	  0.001209	  0.001867	  0.001988	  0.001631	  0.001957	  0.001297	  0.000281	0.001320
      compress_ratio	  0.125007	  0.250007	  0.400007	  0.500007	  0.666674	  0.800007	  0.888899	  1.000007	
         ShiftPacker	       yes	       yes	       yes	       yes	       yes	       yes	       yes	       yes	
        packing(sec)	  0.000463	  0.005479	  0.007083	  0.005532	  0.008202	  0.011867	  0.019691	  0.001964	0.007535
      unpacking(sec)	  0.000326	  0.004567	  0.004572	  0.004333	  0.005266	  0.006249	  0.014632	  0.000250	0.005024
      compress_ratio	  0.125007	  0.250007	  0.400007	  0.500007	  0.666674	  0.800007	  0.888899	  1.000007	
         NumbaPacker	       yes	       yes	       yes	       yes	       yes	       yes	       yes	       yes	
        packing(sec)	  0.002057	  0.003334	  0.004738	  0.006978	  0.008571	  0.009800	  0.011455	  0.013430	0.007545
      unpacking(sec)	  0.002334	  0.004074	  0.005839	  0.007523	  0.009717	  0.011221	  0.012994	  0.015966	0.008708
      compress_ratio	  0.125007	  0.250007	  0.375007	  0.500007	  0.625007	  0.750007	  0.875007	  1.000007	
"""
