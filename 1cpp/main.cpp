#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "CImg.h"
#include <cstdio>
#include <vector>
#include <time.h>
#include <iostream>
#include <bzlib.h>

using namespace cimg_library;

Display* display = nullptr;
Window root_window;
int screen_num;
XWindowAttributes root_attributes;
int width;
int height;
int size;
int depth;
const int C = 4;

static uint8_t gray_lut[256][256][256];
void initGrayLUT() {
    for (int r = 0; r < 256; r++) {
        for (int g = 0; g < 256; g++) {
            for (int b = 0; b < 256; b++) {
                gray_lut[r][g][b] = (r * 77 + g * 150 + b * 29) >> 13;
            }
        }
    }
}

static uint8_t bin_lut[8][8][8][8][8][8][8][8][8];
void initBinLUT() {
    for (int a1 = 0; a1 < 8; a1++) {
        for (int a2 = 0; a2 < 8; a2++) {
            for (int a3 = 0; a3 < 8; a3++) {
                for (int a4 = 0; a4 < 8; a4++) {
                    for (int a5 = 0; a5 < 8; a5++) {
                        for (int a6 = 0; a6 < 8; a6++) {
                            for (int a7 = 0; a7 < 8; a7++) {
                                for (int a8 = 0; a8 < 8; a8++) {
                                    for (int a9 = 0; a9 < 8; a9++) {
                                        bin_lut[a1][a2][a3][a4][a5][a6][a7][a8][a9] = 0;
                                        if (a5 * 9 > a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9 + C) {
                                            bin_lut[a1][a2][a3][a4][a5][a6][a7][a8][a9] = 1;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

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
    size = width * height;

    initGrayLUT();
    initBinLUT();

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
    image = XGetImage(
        display,
        root_window,
        0, 0,
        width, height,
        AllPlanes,
        ZPixmap
    );
    if (!image) {
        fprintf(stderr, "Error: all capture methods failed (depth=%d)\n", depth);
    }
    return image;
}

// Вычисление монохромного изображения
void getMonochromeMap(
    XImage* x_image,
    std::vector<uint8_t>& monochrome_map,
    std::vector<uint8_t>& reference_map,
    int& completed_count,
    int& differenced_count,
    int size_score_th
) {
    const uint8_t* src = reinterpret_cast<const uint8_t*>(x_image->data);
    completed_count = 0;
    differenced_count = 0;

    int size_score = 0;
    uint8_t prev_px = 0; 

    for (int y = 1; y < height - 1; ++y) {
        const uint8_t* prev_row = src + (y - 1) * width * 4;
        const uint8_t* curr_row = src + y * width * 4;
        const uint8_t* next_row = src + (y + 1) * width * 4;
        uint8_t* dest_row = monochrome_map.data() + y * width; // указатель на строку результата
        uint8_t* reference_row = reference_map.data() + y * width;

        for (int x = 4; x < width - 1; x + 4) {
            uint8_t a1 = gray_lut[prev_row[x - 1]][prev_row[x - 1] + 1][prev_row[x - 1] + 2];
            uint8_t a2 = gray_lut[prev_row[x]][prev_row[x] + 1][prev_row[x] + 2];
            uint8_t a3 = gray_lut[prev_row[x + 1]][prev_row[x + 1] + 1][prev_row[x + 1] + 2];
            uint8_t a4 = gray_lut[curr_row[x - 1]][prev_row[x - 1] + 1][prev_row[x - 1] + 2];
            uint8_t a5 = gray_lut[curr_row[x]][prev_row[x] + 1][prev_row[x] + 2];
            uint8_t a6 = gray_lut[curr_row[x + 1]][prev_row[x + 1] + 1][prev_row[x + 1] + 2];
            uint8_t a7 = gray_lut[next_row[x - 1]][prev_row[x - 1] + 1][prev_row[x - 1] + 2];
            uint8_t a8 = gray_lut[next_row[x]][prev_row[x] + 1][prev_row[x] + 2];
            uint8_t a9 = gray_lut[next_row[x + 1]][prev_row[x + 1] + 1][prev_row[x + 1] + 2];
            uint8_t px = bin_lut[a1][a2][a3][a4][a5][a6][a7][a8][a9];
            completed_count += 1;

            if (reference_row[x] != px) {
                reference_row[x] = px;
                dest_row[x] = 1;
                differenced_count += 1;
            }

            if (dest_row[x] != prev_px) {
                prev_px = dest_row[x];
                size_score += 1;
            }
            if (size_score > size_score_th) break;
        }
        if (size_score > size_score_th) break;
    }
}

void compressWithBzip2(
    const std::vector<uint8_t>& data,
    std::vector<uint8_t>& compressed_buffer,
    size_t& compressed_size
) {
    if (data.empty()) {
        compressed_buffer.clear();
        compressed_size = 0;
        return;
    }

    compressed_buffer.resize(data.size() * 1.02 + 600);
    unsigned int temp_size = static_cast<unsigned int>(compressed_buffer.size());
    int bz_error;

    bz_error = BZ2_bzBuffToBuffCompress(
        reinterpret_cast<char*>(compressed_buffer.data()),
        &temp_size,
        reinterpret_cast<char*>(const_cast<unsigned char*>(data.data())),
        static_cast<unsigned int>(data.size()),
        9, 0, 30
    );

    if (bz_error != BZ_OK) {
        throw std::runtime_error("Bzip2 compression failed with error code: " + std::to_string(bz_error));
    }

    compressed_buffer.resize(temp_size);
    compressed_size = temp_size;
}

// Конвертация monochrome в CImg<unsigned char>
CImg<unsigned char> monochrome_to_cimg(const std::vector<uint8_t>& monochrome_map) {
    // Проверка корректности размеров
    if (monochrome_map.size() != static_cast<size_t>(width * height)) {
        throw std::invalid_argument("Data size does not match image dimensions");
    }

    // Создаём CImg: одноканальное чёрно‑белое изображение
    // width × height, 1 слой, 1 канал (grayscale)
    CImg<unsigned char> cimg(width, height, 1, 1);

    // Заполняем пиксели: 0 → 0 (чёрный), 1 → 255 (белый)
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            size_t index = static_cast<size_t>(y * width + x);
            unsigned char pixel_value = (monochrome_map[index] == 0) ? 0 : 255;
            cimg(x, y, 0, 0) = pixel_value;
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

int main() {    
    if (!init_x11()) { return false; }
    std::vector<uint8_t> reference_map(size, 0);

    // Capture
    clock_t start = clock();
    XImage* x_image = capture_screen_image();
    if (!x_image) {
        cleanup_x11();
        return false;
    }

    // Processing
    std::vector<uint8_t> monochrome_map(size, 0);
    int completed_count;
    int differenced_count;
    getMonochromeMap(x_image, monochrome_map, reference_map, completed_count, differenced_count, 200000);
    XDestroyImage(x_image);
    cleanup_x11();
    
    // Compressing
    std::vector<uint8_t> output_buffer;
    size_t output_size;
    compressWithBzip2(monochrome_map, output_buffer, output_size);

    int proc_time = (clock() - start) * 1000 / CLOCKS_PER_SEC; // в мс
    save_to_bmp(monochrome_to_cimg(monochrome_map), "test.bmp");
    std::cout << output_size << " B" << "\n";
    std::cout << proc_time << " ms" << "\n";
}