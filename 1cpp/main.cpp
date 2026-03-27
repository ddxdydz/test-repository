#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "CImg.h"
#include <cstdio>
#include <vector>
#include <time.h>
#include <iostream>
#include <bzlib.h>
#include <cstring>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

using namespace cimg_library;

Display* display = nullptr;
Window root_window;
int screen_num;
XWindowAttributes root_attributes;
int width;
int height;
int size;

static uint8_t gray_lut[256 * 256 * 256];
void initGrayLUT() {
    for (int r = 0; r < 256; r++) {
        for (int g = 0; g < 256; g++) {
            for (int b = 0; b < 256; b++) {
                gray_lut[(r << 16) | (g << 8) | b] = (r * 299 + g * 587 + b * 114) >> 10;
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
    size = width * height;

    initGrayLUT();

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
    XImage* image = XGetImage(
        display,
        root_window,
        0, 0,
        width, height,
        AllPlanes,
        ZPixmap
    );
    if (!image) {
        fprintf(stderr, "Error: capture methods failed\n");
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
    int size_score_th,
    int threshold
) {
    const uint32_t* src = reinterpret_cast<const uint32_t*>(x_image->data);
    completed_count = 0;
    differenced_count = 0;

    int size_score = 0;
    uint8_t prev_px = 0;

    for (int y = 1; y < height - 1; ++y) {
        const uint32_t* curr_row = src + y * width;
        uint8_t* dest_row = monochrome_map.data() + y * width;
        uint8_t* reference_row = reference_map.data() + y * width;

        for (int x = 1; x < width - 1; ++x) {
            uint8_t px = (threshold > gray_lut[curr_row[x] >> 8]) ? 1 : 0;
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

// Функция для надёжной отправки данных (гарантирует отправку всех байтов)
ssize_t reliable_send(int sockfd, const void* buf, size_t len) {
    const uint8_t* ptr = static_cast<const uint8_t*>(buf);
    size_t total_sent = 0;

    while (total_sent < len) {
        ssize_t sent = send(sockfd, ptr + total_sent, len - total_sent, 0);
        if (sent == -1) {
            perror("send failed");
            return -1;
        }
        if (sent == 0) {
            // Клиент отключился
            std::cout << "Client disconnected during send\n";
            return 0;
        }
        total_sent += sent;
    }
    return total_sent;
}

// Функция для генерации массива
std::vector<uint8_t> generate_array() {
    std::vector<uint8_t> monochrome_map(1263, 0);
    // Заполняем массив какими‑то данными (для примера — последовательность)
    for (size_t i = 0; i < monochrome_map.size(); ++i) {
        monochrome_map[i] = static_cast<uint8_t>(i % 256);
    }
    return monochrome_map;
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

// Сохранение изображения в BMP через CImg
bool screen() {
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
    getMonochromeMap(x_image, monochrome_map, reference_map, completed_count, differenced_count, 20000, 155);
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

bool server() {
    if (!init_x11()) { return false; }
    std::vector<uint8_t> reference_map(size, 0);

    int server_fd, client_fd;
    struct sockaddr_in address;
    int opt = 1;
    socklen_t addrlen = sizeof(address);

    // Создаём сокет
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Устанавливаем опцию SO_REUSEADDR
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("setsockopt failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8888);

    // Привязываем сокет к адресу
    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("bind failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // Слушаем входящие соединения (только одно соединение в очереди)
    if (listen(server_fd, 1) < 0) {
        perror("listen failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    std::cout << "Server listening on port 8080...\n";

    // Принимаем единственное соединение
    if ((client_fd = accept(server_fd, (struct sockaddr*)&address, &addrlen)) < 0) {
        perror("accept failed");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    std::cout << "Client connected\n";

    // Основной цикл работы
    while (true) {
        // Ждём запрос от клиента (простой приём одного байта как сигнала)
        char request;
        ssize_t bytes_received = recv(client_fd, &request, 1, 0);

        if (bytes_received <= 0) {
            // Клиент отключился или ошибка
            if (bytes_received == 0) {
                std::cout << "Client disconnected\n";
            } else {
                perror("recv failed");
            }
            break;
        }

        // Генерируем массив
        // Capture
        clock_t start = clock();
        XImage* x_image = capture_screen_image();
        if (!x_image) {cleanup_x11(); return false;}
        // Processing
        std::vector<uint8_t> monochrome_map(size, 0);
        int completed_count;
        int differenced_count;
        getMonochromeMap(x_image, monochrome_map, reference_map, completed_count, differenced_count, 20000, 155);
        XDestroyImage(x_image);
        cleanup_x11();
        // Compressing
        std::vector<uint8_t> output_buffer;
        size_t output_size;
        compressWithBzip2(monochrome_map, output_buffer, output_size);
        uint32_t data_size = static_cast<uint32_t>(output_size);
        int proc_time = (clock() - start) * 1000 / CLOCKS_PER_SEC; // в мс
        std::cout << output_size << " B" << "\n";
        std::cout << proc_time << " ms" << "\n";

        // Отправляем заголовок (4 байта с длиной массива)
        uint32_t network_size = htonl(data_size);
        if (reliable_send(client_fd, &network_size, sizeof(network_size)) <= 0) {
            break;
        }

        // Отправляем сам массив
        if (reliable_send(client_fd, output_buffer.data(), output_buffer.size()) <= 0) {
            break;
        }

        std::cout << "Sent array of " << data_size << " bytes\n";
    }

    // Закрываем соединения
    close(client_fd);
    close(server_fd);

    std::cout << "Server terminated\n";
    return 0;
}

int main() {    
    server();
}