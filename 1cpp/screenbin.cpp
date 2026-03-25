#include <opencv4/opencv2/opencv.hpp>  // Сначала OpenCV
#include <X11/Xlib.h>                  // Потом X11
#include <X11/Xutil.h>
#include "CImg.h"
#include <cstdio>
#include <vector>
#include <time.h>
#include <iostream>

using namespace cimg_library;

// Глобальные переменные
Display* display = nullptr;
Window root_window;
int screen_num;
XWindowAttributes root_attributes;
int width;
int height;
int depth;

// Инициализация X11 соединения
bool init_x11() {
    display = XOpenDisplay(nullptr);
    if (!display) {
        fprintf(stderr, "Error: cannot open display\n");
        return false;
    }

    screen_num = DefaultScreen(display);
    root_window = RootWindow(display, screen_num);

    if (!XGetWindowAttributes(display, root_window, &root_attributes)) {
        fprintf(stderr, "Error: cannot get window attributes\n");
        XCloseDisplay(display);
        display = nullptr;
        return false;
    }

    width = root_attributes.width;
    height = root_attributes.height;
    depth = root_attributes.depth;

    return true;
}

// Освобождение ресурсов X11
void cleanup_x11() {
    if (display) {
        XCloseDisplay(display);
        display = nullptr;
    }
}

// Захват экрана и возврат XImage
XImage* capture_screen_image() {
    XImage* image = nullptr;

    // Вариант 1: стандартный захват
    image = XGetImage(
        display,
        root_window,
        0, 0,
        width, height,
        AllPlanes,
        ZPixmap
    );

    if (image) return image;

    // Вариант 2: с явным указанием визуала и глубины
    image = XGetImage(
        display,
        root_window,
        0, 0,
        width, height,
        AllPlanes,
        XYPixmap
    );

    if (image) return image;

    if (!image) {
        fprintf(stderr, "Error: all capture methods failed (depth=%d)\n", depth);
    }
    return image;
}

// Конвертация XImage в cv::Mat

cv::Mat ximage_to_mat_optimized(XImage* x_image) {
    // Создаём временную матрицу RGBA
    cv::Mat rgba(x_image->height, x_image->width, CV_8UC4);
    memcpy(rgba.data, x_image->data, x_image->height * x_image->bytes_per_line);

    // Удаляем альфа‑канал и меняем порядок на BGR
    cv::Mat bgr;
    cv::cvtColor(rgba, bgr, cv::COLOR_RGBA2BGR);
    return bgr;
}

cv::Mat ximage_to_mat_optimized2(XImage* x_image) {
    cv::Mat bgr(x_image->height, x_image->width, CV_8UC3);
    const uint32_t* src = reinterpret_cast<const uint32_t*>(x_image->data);
    uint8_t* dst = bgr.data;

    for (int y = 0; y < x_image->height; ++y) {
        for (int x = 0; x < x_image->width; ++x) {
            uint32_t pixel = src[y * x_image->width + x];
            dst[0] = static_cast<uint8_t>(pixel);        // B
            dst[1] = static_cast<uint8_t>(pixel >> 8);  // G
            dst[2] = static_cast<uint8_t>(pixel >> 16); // R
            dst += 3;
        }
    }
    return bgr;
}

cv::Mat ximage_to_mat(XImage* x_image) {
    int width = x_image->width;
    int height = x_image->height;
    cv::Mat mat(height, width, CV_8UC3);
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            unsigned long pixel = XGetPixel(x_image, x, y);
            uchar r = (pixel >> 16) & 0xFF;
            uchar g = (pixel >> 8) & 0xFF;
            uchar b = pixel & 0xFF;
            mat.at<cv::Vec3b>(y, x) = cv::Vec3b(b, g, r);
        }
    }
    return mat;
}

// Квантизация через OpenCV (метод Оцу)
cv::Mat quantize_with_opencv(cv::Mat image) {
    // Переводим в градации серого
    cv::cvtColor(image, image, cv::COLOR_BGR2GRAY);
    // Применяем бинаризацию с методом Оцу
    cv::threshold(image, image, 0, 255, cv::THRESH_BINARY + cv::THRESH_OTSU);
    return image;
}


cv::Mat quantize_fast_adaptive(cv::Mat image) {
    cv::Mat gray, result;

    // Переводим в градации серого
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);

    // Адаптивная бинаризация — автоматически подбирает порог для каждой области
    cv::adaptiveThreshold(gray, result, 255,
                       cv::ADAPTIVE_THRESH_MEAN_C,
                       cv::THRESH_BINARY,
                       3,  // размер окрестности (чем меньше, тем быстрее) (% 2 != 0)
                       -2); // константа вычитания

    return result;
}

// Конвертация cv::Mat в CImg<unsigned char> для сохранения через CImg
CImg<unsigned char> mat_to_cimg(const cv::Mat& mat) {
    int width = mat.cols;
    int height = mat.rows;

    // CImg: одноканальное изображение для бинарного результата
    CImg<unsigned char> cimg(width, height, 1, 1);

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            cimg(x, y, 0, 0) = mat.at<uchar>(y, x);
        }
    }
    return cimg;
}

// Конвертация XImage в CImg<unsigned char>
CImg<unsigned char> ximage_to_cimg(XImage* x_image) {
    int width = x_image->width;
    int height = x_image->height;

    // CImg: RGB, 3 канала
    CImg<unsigned char> cimg(width, height, 1, 3);

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            unsigned long pixel = XGetPixel(x_image, x, y);
            cimg(x, y, 0, 0) = (pixel >> 16) & 0xFF; // R
            cimg(x, y, 0, 1) = (pixel >> 8)  & 0xFF; // G
            cimg(x, y, 0, 2) = pixel         & 0xFF; // B
        }
    }
    return cimg;
}

// Сохранение изображения в BMP через CImg
bool save_to_bmp(const CImg<unsigned char>& image, const char* filename) {
    try {
        image.save_bmp(filename);
        return true;
    } catch (const CImgException& e) {
        fprintf(stderr, "Error saving BMP: %s\n", e.what());
        return false;
    }
}

// Основная функция захвата, квантизации и сохранения скриншота
bool take_screenshot_quantize_and_save(const char* output_filename) {
    if (!init_x11()) { return false; }

    // Capture
    clock_t start = clock();
    XImage* x_image = capture_screen_image();
    if (!x_image) {
        cleanup_x11();
        return false;
    }
    std::cout << "Capture time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";

    // Конвертируем XImage в OpenCV Mat
    // start = clock();
    // image = ximage_to_mat(x_image);
    // std::cout << "Convert time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";
    // start = clock();
    // image = ximage_to_mat_optimized(x_image);
    // std::cout << "Convert O time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";
    start = clock();
    cv::Mat image = ximage_to_mat_optimized2(x_image);
    std::cout << "Convert O2 time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";

     // Квантизация через OpenCV
    start = clock();
    cv::Mat quantized_mat = quantize_fast_adaptive(image);
    std::cout << "Quantization time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";

    // Конвертация результата в CImg для сохранения
    CImg<unsigned char> quantized_cimg = mat_to_cimg(quantized_mat);
    XDestroyImage(x_image);

    // Cleanup x11
    start = clock();
    cleanup_x11();
    std::cout << "Cleanup time: " << ((double)(clock() - start) / CLOCKS_PER_SEC) << "s\n";

    bool success = save_to_bmp(quantized_cimg, output_filename);
    return success;
}

int main() {
    const char* filename = "test.bmp";

    if (take_screenshot_quantize_and_save(filename)) {
        printf("Quantized screenshot saved as '%s'\n", filename);
        return 0;
    } else {
        fprintf(stderr, "Failed to capture and quantize screenshot\n");
        return 1;
    }
}