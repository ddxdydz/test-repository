#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "CImg.h"
#include <cstdio>
#include <vector>
#include <time.h>
#include <iostream>
#include <bzlib.h>
#include <emmintrin.h>

using namespace cimg_library;

Display* display = nullptr;
Window root_window;
int screen_num;
XWindowAttributes root_attributes;
int width;
int height;
int size;
int depth;
const int C = 2;

static uint8_t gray_lut[256 * 256 * 256];
void initGrayLUT() {
    for (int r = 0; r < 256; r++) {
        for (int g = 0; g < 256; g++) {
            for (int b = 0; b < 256; b++) {
                gray_lut[(r << 16) | (g << 8) | b] = (r * 77 + g * 150 + b * 29) >> 15;
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
    const uint32_t* src = reinterpret_cast<const uint32_t*>(x_image->data);
    completed_count = 0;
    differenced_count = 0;

    int size_score = 0;
    uint8_t prev_px = 0;

    const int simd_width = (width - 2) & ~15; // Округление до кратного 16

    for (int y = 1; y < height - 1; ++y) {
        const uint32_t* curr_row = src + y * width;
        uint8_t* dest_row = monochrome_map.data() + y * width;
        uint8_t* reference_row = reference_map.data() + y * width;

        for (int x = 1; x < simd_width; x += 16) {
            // Загрузка 4 пикселей (32-битных) за раз — всего 16 байт
            __m128i pixels1 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(curr_row + x));

            // Извлечение старших байтов (компонент цвета) через сдвиги и маски
            __m128i bytes = _mm_srli_epi32(pixels1, 8); // Сдвиг вправо на 8 бит
            bytes = _mm_and_si128(bytes, _mm_set1_epi32(0xFF)); // Маска для выделения байта

            // Преобразование в 8-битные значения через pack
            __m128i packed = _mm_packs_epi32(_mm_srli_epi64(bytes, 8), bytes);
            __m128i gray8 = _mm_packus_epi16(packed, packed);

            // Загрузка эталонных пикселей
            __m128i ref_pixels = _mm_loadu_si128(reinterpret_cast<const __m128i*>(reference_row + x));

            // Сравнение: получаем маску где gray8 != ref_pixels
            __m128i diff_mask = _mm_cmpeq_epi8(gray8, ref_pixels);
            diff_mask = _mm_xor_si128(diff_mask, _mm_set1_epi8(-1)); // Инверсия: 0 → -1, -1 → 0

            // Подсчёт различий через горизонтальное суммирование
            int mask = _mm_movemask_epi8(diff_mask);
            int diff_count = __builtin_popcount(mask); // Подсчёт единиц в битовой маске
            differenced_count += diff_count;

            // Обновление эталонных значений: используем побитовые операции вместо _mm_blendv_epi8
            __m128i updated_ref = _mm_or_si128(
                _mm_and_si128(ref_pixels, _mm_xor_si128(diff_mask, _mm_set1_epi8(-1))),
                _mm_and_si128(gray8, diff_mask)
            );
            _mm_storeu_si128(reinterpret_cast<__m128i*>(reference_row + x), updated_ref);

            // Формирование монохромной карты: 1 там, где есть различия
            __m128i mono_pixels = _mm_slli_epi32(diff_mask, 7); // Сдвиг для получения 0/1
            mono_pixels = _mm_srli_epi32(mono_pixels, 7);
            _mm_storeu_si128(reinterpret_cast<__m128i*>(dest_row + x), mono_pixels);

            completed_count += 16;

            // Обработка size_score (скалярная часть)
            for (int i = 0; i < 16; ++i) {
                uint8_t current = ((uint8_t*)&mono_pixels)[i];
                if (current != prev_px) {
                    prev_px = current;
                    size_score += 1;
                }
                if (size_score > size_score_th) break;
            }
            if (size_score > size_score_th) break;
        }

        // Скалярная обработка остатка строки
        for (int x = simd_width + 1; x < width - 1; ++x) {
            uint8_t px = gray_lut[curr_row[x] >> 8];
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
    getMonochromeMap(x_image, monochrome_map, reference_map, completed_count, differenced_count, 20000);
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