#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "CImg.h"
#include <cstdio>
#include <vector>
#include <time.h> 
#include <iostream>

using namespace cimg_library;

// Глобальные переменные (для простоты, можно передавать как параметры)
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
    // Пробуем разные варианты захвата
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

// Конвертация XImage в CImg<unsigned char>
CImg<unsigned char> ximage_to_cimg(XImage* x_image) {
    int width = x_image->width;
    int height = x_image->height;

    // CImg: RGB, 3 канала
    CImg<unsigned char> cimg(width, height, 1, 3);

    #pragma omp parallel for
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

// Основная функция захвата и сохранения скриншота
bool take_screenshot_and_save(const char* output_filename) {
    if (!init_x11()) { return false; }

    clock_t start = clock();
    XImage* x_image = capture_screen_image();
    if (!x_image) {
        cleanup_x11();
        return false;
    }
    std::cout << ((double)(clock() - start) / CLOCKS_PER_SEC) << std::endl;

    start = clock();
    x_image = capture_screen_image();
    if (!x_image) {
        cleanup_x11();
        return false;
    }
    std::cout << ((double)(clock() - start) / CLOCKS_PER_SEC) << std::endl;

    start = clock();
    x_image = capture_screen_image();
    if (!x_image) {
        cleanup_x11();
        return false;
    }
    std::cout << ((double)(clock() - start) / CLOCKS_PER_SEC) << std::endl;

    start = clock();
    CImg<unsigned char> cimg = ximage_to_cimg(x_image);
    XDestroyImage(x_image);
    std::cout << ((double)(clock() - start) / CLOCKS_PER_SEC) << std::endl;

    start = clock();
    cleanup_x11();
    std::cout << ((double)(clock() - start) / CLOCKS_PER_SEC) << std::endl;

    bool success = save_to_bmp(cimg, output_filename);

    return success;
}

int main() {
    const char* filename = "screenshot.bmp";

    if (take_screenshot_and_save(filename)) {
        printf("Screenshot saved as '%s'\n", filename);
        return 0;
    } else {
        fprintf(stderr, "Failed to capture screenshot\n");
        return 1;
    }
}
