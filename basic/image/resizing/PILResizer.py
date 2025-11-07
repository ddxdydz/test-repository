from PIL import Image

from basic.image.resizing.support.ImageResizer import ImageResizer
from basic.image.resizing.support.ResizeMethod import ResizeMethod
from basic.image.resizing.support.ResizeTask import ResizeTask


class PILResizer(ImageResizer):
    """Реализация изменения размера с использованием PIL"""

    def resize(self, image: Image.Image, resize_task: ResizeTask) -> Image.Image:
        """
        Изменяет размер изображения согласно задаче

        Args:
            image: Исходное изображение PIL
            resize_task: Задача изменения размера

        Returns:
            Измененное изображение PIL
        """
        # Вычисляем целевой размер
        target_size = resize_task.calculate_size(image.size)

        # Конвертируем в RGB если нужно (для корректной работы с JPEG)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Изменяем размер
        resized_img = image.resize(target_size, self._get_pil_resample())

        return resized_img


if __name__ == "__main__":
    s = []
    k = []
    for i in range(1, 10):
        s.append(i / 10)
        k.append(round((1 / (i / 10)) ** 2, 2))
    print(*s, sep='\t\t')
    print(*k, sep='\t')

    temp_path = r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\resizing\temp"
    path = r"C:\Users\UserLog.ru\PycharmProjects\regular\basic\image\data\v10.png"
    img_type = path[path.rfind("."):]
    input_image = Image.open(path)
    scale = 0.7
    show = True

    resizer = PILResizer()
    resize_task = ResizeTask(scale=scale)
    desize_task = ResizeTask(scale=1 / scale)

    from time import time

    resizer.method = ResizeMethod.NEAREST
    start_time = time()
    resized_img1 = resizer.resize(input_image, resize_task)
    resize_time = time() - start_time
    start_time = time()
    desized_img1 = resizer.resize(resized_img1, desize_task)
    desize_time = time() - start_time
    print(f"{resizer.method.name}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")
    input_image.save(f"{temp_path}/1 0{img_type}")
    desized_img1.save(f"{temp_path}/1 NEAREST{img_type}")

    resizer.method = ResizeMethod.AREA
    start_time = time()
    resized_img2 = resizer.resize(input_image, resize_task)
    resize_time = time() - start_time
    start_time = time()
    desized_img2 = resizer.resize(resized_img2, desize_task)
    desize_time = time() - start_time
    print(f"{resizer.method.name}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")
    # input_image.save(f"{temp_path}/2 0{img_type}")
    desized_img2.save(f"{temp_path}/2 AREA{img_type}")

    resizer.method = ResizeMethod.BILINEAR
    start_time = time()
    resized_img3 = resizer.resize(input_image, resize_task)
    resize_time = time() - start_time
    start_time = time()
    desized_img3 = resizer.resize(resized_img3, desize_task)
    desize_time = time() - start_time
    print(f"{resizer.method.name}\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")
    # input_image.save(f"{temp_path}/3 0{img_type}")
    desized_img3.save(f"{temp_path}/3 BILINEAR{img_type}")

    resizer.method = ResizeMethod.BICUBIC
    start_time = time()
    resized_img4 = resizer.resize(input_image, resize_task)
    resize_time = time() - start_time
    start_time = time()
    desized_img4 = resizer.resize(resized_img4, desize_task)
    desize_time = time() - start_time
    print(f"{resizer.method.name}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")
    # input_image.save(f"{temp_path}/4 0{img_type}")
    desized_img4.save(f"{temp_path}/4 BICUBIC{img_type}")

    resizer.method = ResizeMethod.LANCZOS
    start_time = time()
    resized_img5 = resizer.resize(input_image, resize_task)
    resize_time = time() - start_time
    start_time = time()
    desized_img5 = resizer.resize(resized_img5, desize_task)
    desize_time = time() - start_time
    print(f"{resizer.method.name}\t\tresize_time={resize_time} c\t\tdesize_time={desize_time} c")
    # input_image.save(f"{temp_path}/5 0{img_type}")
    desized_img5.save(f"{temp_path}/5 LANCZOS{img_type}")

    resized_img = resized_img5

    im_size, im_count_px = input_image.size, input_image.width * input_image.height
    rim_size, rim_count_px = resized_img.size, resized_img.width * resized_img.height
    print(im_size, im_count_px)
    print(rim_size, rim_count_px)
    print(f"{round((rim_count_px / im_count_px) * 100, 2)} %", round(im_count_px / rim_count_px, 2))
