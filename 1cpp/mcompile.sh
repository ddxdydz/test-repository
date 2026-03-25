g++ -Wall -Wextra -g3 -fopenmp main.cpp -o main.exe \
    $(pkg-config --cflags --libs opencv4) -lbz2 -lX11
