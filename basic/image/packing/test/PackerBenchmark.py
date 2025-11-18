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
        print(np.prod(data_for_speed_test), data_for_speed_test, f"iterations={iterations}")
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
        packing(sec)	  0.000398	  0.002230	  0.003542	  0.001677	  0.003887	  0.005066	  0.007511	  0.001155	0.003183
      unpacking(sec)	  0.000221	  0.001034	  0.001268	  0.001336	  0.001152	  0.001231	  0.001023	  0.000181	0.000931
      compress_ratio	  0.125007	  0.250007	  0.400007	  0.500007	  0.666674	  0.800007	  0.888899	  1.000007	
         ShiftPacker	       yes	       yes	       yes	       yes	       yes	       yes	       yes	       yes	
        packing(sec)	  0.000354	  0.003762	  0.004726	  0.003742	  0.005323	  0.006845	  0.012456	  0.001044	0.004782
      unpacking(sec)	  0.000219	  0.003056	  0.003603	  0.002980	  0.004960	  0.007007	  0.009924	  0.000143	0.003987
      compress_ratio	  0.125007	  0.250007	  0.400007	  0.500007	  0.666674	  0.800007	  0.888899	  1.000007	
         NumbaPacker	       yes	       yes	       yes	       yes	       yes	       yes	       yes	       yes	
        packing(sec)	  0.001034	  0.001542	  0.002297	  0.003532	  0.004357	  0.004984	  0.005846	  0.006955	0.003818
      unpacking(sec)	  0.001096	  0.001758	  0.002824	  0.003582	  0.004433	  0.005014	  0.006185	  0.007077	0.003996
      compress_ratio	  0.125007	  0.250007	  0.375007	  0.500007	  0.625007	  0.750007	  0.875007	  1.000007	
"""
