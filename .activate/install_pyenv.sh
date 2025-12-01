#!/bin/bash

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Установка системных зависимостей для PYTHON

# Для корректной компиляции для низкоуровневых библиотек
sudo apt install -y python3-dev build-essential cmake pkg-config

# Зависимости для научных вычислений
sudo apt install -y libatlas-base-dev gfortran

# Зависимости OpenCV
sudo apt install -y libopencv-dev libgtk-3-dev libavcodec-dev libavformat-dev \
    libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libjpeg-dev \
    libpng-dev libtiff-dev libopenexr-dev libtbb2 libtbb-dev libdc1394-dev

# Зависимости PyGame и GUI
sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev \
    libsdl2-ttf-dev libportmidi-dev libfreetype6-dev libx11-dev \
    libxcursor-dev libxrandr-dev libxinerama-dev libxi-dev \
    libgl1-mesa-dev libgles2-mesa-dev libegl1-mesa-dev \
    libdbus-1-dev libharfbuzz-dev

# Pyautogui
sudo apt-get install python3-tk python3-dev -y
sudo apt install gnome-screenshot

# Зависимости Numba
sudo apt install -y llvm-dev llvm libllvm16

# Аудио зависимости
sudo apt install -y libasound2-dev libpulse-dev

# Очистка кеша
sudo apt autoremove -y

# Установка python
sudo apt install python3 python3-pip python3-venv -y

# Создание и активация среды
python3 -m venv ~/test-repository/pyenv
echo 'source ~/test-repository/pyenv/bin/activate' >> ~/.bashrc
source ~/test-repository/pyenv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r ~/test-repository/requirements.txt
