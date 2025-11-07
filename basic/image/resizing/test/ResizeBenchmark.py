import statistics
import time
from typing import Optional, Dict, List

from PIL import Image

from basic.image.resizing.support.ImageResizer import ImageResizer
from basic.image.resizing.PILResizer import PILResizer
from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.support.ResizeTask import ResizeTask


class ResizeBenchmark:
    """Класс для оценки производительности методов изменения размера"""

    def __init__(self):
        self.results = {}

    def benchmark_resizer(self,
                          resizer: ImageResizer,
                          image: Image.Image,
                          resize_task: ResizeTask,
                          iterations: int = 5) -> Optional[Dict]:
        """
        Тестирование производительности ресайзера

        Args:
            resizer: Объект ресайзера
            image: Тестовое изображение
            resize_task: Задача изменения размера
            iterations: Количество итераций

        Returns:
            Словарь с результатами или None при ошибке
        """
        print(f"Тестирование {resizer} с задачей {resize_task}...")

        # Проверяем, что ресайзер работает
        try:
            test_result = resizer.resize(image, resize_task)
            expected_size = resize_task.calculate_size(image.size)
            if test_result.size != expected_size:
                raise ValueError(f"Некорректный размер результата: {test_result.size} != {expected_size}")
        except Exception as e:
            print(f"Ошибка в ресайзере {resizer}: {e}")
            return None

        # Измеряем время выполнения
        times = []
        for i in range(iterations):
            start_time = time.time()
            try:
                _ = resizer.resize(image, resize_task)
                end_time = time.time()
                times.append(end_time - start_time)
            except Exception as e:
                print(f"Ошибка на итерации {i + 1}: {e}")
                continue

        if not times:
            print("Не удалось выполнить ни одной итерации")
            return None

        # Вычисляем метрики
        avg_time = statistics.mean(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        min_time = min(times)
        max_time = max(times)

        result = {
            'resizer': str(resizer),
            'method': resizer.method.value,
            'resize_task': str(resize_task),
            'avg_time_ms': avg_time * 1000,
            'std_time_ms': std_time * 1000,
            'min_time_ms': min_time * 1000,
            'max_time_ms': max_time * 1000,
            'iterations': len(times),
            'original_size': image.size,
            'target_size': resize_task.calculate_size(image.size),
            'image_mode': image.mode,
            'times': times
        }

        # Сохраняем результат
        key = f"{resizer.__class__.__name__}_{resizer.method.value}_{hash(str(resize_task))}"
        self.results[key] = result

        return result

    def compare_methods(self,
                        image: Image.Image,
                        resize_task: ResizeTask,
                        iterations: int = 5) -> List[Dict]:
        """
        Сравнение всех доступных методов

        Returns:
            Список результатов для всех протестированных методов
        """
        all_results = []

        resizer_class = PILResizer
        for method in ResizeMethod:
            try:
                resizer = resizer_class(method)
                result = self.benchmark_resizer(resizer, image, resize_task, iterations)
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"Ошибка при тестировании {resizer_class.__name__} {method}: {e}")

        # Сортируем по времени выполнения
        all_results.sort(key=lambda x: x['avg_time_ms'])

        return all_results

    def compare_tasks(self,
                      image: Image.Image,
                      resize_tasks: List[ResizeTask],
                      method: ResizeMethod = ResizeMethod.BILINEAR,
                      iterations: int = 3) -> List[Dict]:
        """
        Сравнение производительности для разных задач изменения размера
        """
        all_results = []

        for task in resize_tasks:
            try:
                resizer = PILResizer(method)
                result = self.benchmark_resizer(resizer, image, task, iterations)
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"Ошибка при тестировании задачи {task}: {e}")

        return all_results

    def print_results(self, results: List[Dict] = None):
        """Вывод результатов в читаемом формате"""
        if results is None:
            results = [self.results[key] for key in sorted(self.results.keys())]

        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ МЕТОДОВ ИЗМЕНЕНИЯ РАЗМЕРА")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['resizer']}")
            print(f"   Задача: {result['resize_task']}")
            print(f"   Среднее время: {result['avg_time_ms']:.3f} ms")
            print(f"   Стандартное отклонение: {result['std_time_ms']:.3f} ms")
            print(f"   Диапазон: {result['min_time_ms']:.3f}-{result['max_time_ms']:.3f} ms")
            print(f"   Итерации: {result['iterations']}")
            print(f"   Размер: {result['original_size']} -> {result['target_size']}")
            print(f"   Режим изображения: {result['image_mode']}")

    def generate_report(self, results: List[Dict] = None) -> str:
        """Генерация текстового отчета"""
        if results is None:
            results = [self.results[key] for key in sorted(self.results.keys())]

        report = ["ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ РЕСАЙЗЕРОВ", "=" * 50]

        for i, result in enumerate(results, 1):
            report.append(f"\n{i}. {result['resizer']}")
            report.append(f"   Метод: {result['method']}")
            report.append(f"   Задача: {result['resize_task']}")
            report.append(f"   Среднее время: {result['avg_time_ms']:.3f} ms")
            report.append(f"   Отклонение: ±{result['std_time_ms']:.3f} ms")
            report.append(f"   Размер: {result['original_size']} -> {result['target_size']}")

        # Лучший результат
        if results:
            best = results[0]
            report.append(f"\nЛУЧШИЙ РЕЗУЛЬТАТ:")
            report.append(f"Метод: {best['resizer']}")
            report.append(f"Задача: {best['resize_task']}")
            report.append(f"Время: {best['avg_time_ms']:.3f} ms")

        return "\n".join(report)


def create_test_image(width: int = 800, height: int = 600) -> Image.Image:
    """Создание тестового изображения"""
    from PIL import ImageDraw

    # Создаем новое изображение
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Рисуем простые фигуры для создания тестового изображения
    # Прямоугольник
    draw.rectangle([50, 50, width - 50, height - 50], outline='red', width=5)

    # Круг
    draw.ellipse([width // 4, height // 4, 3 * width // 4, 3 * height // 4], outline='blue', width=5)

    # Текст
    try:
        from PIL import ImageFont
        # Попробуем использовать стандартный шрифт
        font = ImageFont.load_default()
        draw.text((width // 2 - 100, height // 2), "Test Image", fill='green', font=font)
    except:
        draw.text((width // 2 - 100, height // 2), "Test Image", fill='green')

    return img


# Пример использования
def demo():
    """Демонстрация работы классов"""

    # Создаем тестовое изображение
    print("Создание тестового изображения...")
    test_image = create_test_image(800, 600)
    print(f"Создано изображение: {test_image.size}, режим: {test_image.mode}")

    # Создаем различные задачи изменения размера
    resize_tasks = [
        ResizeTask(size=(400, 300)),  # Точный размер
        ResizeTask(scale=0.5),  # Масштаб 50%
        ResizeTask(max_size=(500, 500)),  # Максимальный размер 500x500
        ResizeTask(width=200),  # Фиксированная ширина 200
        ResizeTask(height=150),  # Фиксированная высота 150
    ]

    # Демонстрация работы ресайзеров с разными задачами
    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ РЕСАЙЗЕРОВ С РАЗНЫМИ ЗАДАЧАМИ")
    print("=" * 50)

    for i, task in enumerate(resize_tasks, 1):
        print(f"\n{i}. Задача: {task}")

        # PIL ресайзер
        pil_resizer = PILResizer(ResizeMethod.LANCZOS)
        result_pil = pil_resizer.resize(test_image, task)
        print(f"   PIL Resizer: {test_image.size} -> {result_pil.size}")

    # Бенчмаркинг методов для одной задачи
    print("\n" + "=" * 50)
    print("СРАВНЕНИЕ МЕТОДОВ ДЛЯ ЗАДАЧИ ResizeTask(scale=0.5)")
    print("=" * 50)

    benchmark = ResizeBenchmark()
    task = ResizeTask(scale=0.5)
    results = benchmark.compare_methods(test_image, task, iterations=3)
    benchmark.print_results(results)

    # Сравнение разных задач с одним методом
    print("\n" + "=" * 50)
    print("СРАВНЕНИЕ РАЗНЫХ ЗАДАЧ С МЕТОДОМ BILINEAR")
    print("=" * 50)

    task_results = benchmark.compare_tasks(test_image, resize_tasks,
                                           method=ResizeMethod.BILINEAR,
                                           iterations=2)

    for result in task_results:
        print(f"{result['resize_task']}: {result['avg_time_ms']:.3f} ms "
              f"({result['original_size']} -> {result['target_size']})")

    # Генерация отчета
    print("\n" + "=" * 50)
    print("ФИНАЛЬНЫЙ ОТЧЕТ")
    print("=" * 50)

    report = benchmark.generate_report()
    print(report)

    print("\nДемонстрация завершена!")


if __name__ == "__main__":
    demo()
