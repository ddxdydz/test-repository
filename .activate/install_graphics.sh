#!/bin/bash

# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем XFCE (легковесный рабочий стол) и xorg
sudo apt install xfce4 xfce4-goodies xorg dbus-x11 -y

# Устанавливаем дополнительные программы
sudo apt install chromium-browser gedit mousepad thunar file-roller -y
sudo apt install gnome-terminal synaptic -y


# Создаем автозагрузку X сервера
sudo tee /etc/systemd/system/x11.service > /dev/null << EOF
[Unit]
Description=X11 Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/X :0 vt1 -ac
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF


# Создаем автозагрузку рабочего стола
sudo tee /etc/systemd/system/desktop.service > /dev/null << EOF
[Unit]
Description=XFCE Desktop
After=x11.service
Wants=x11.service

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XDG_SESSION_TYPE=x11
Environment=XDG_CURRENT_DESKTOP=XFCE
ExecStart=/usr/bin/startxfce4
Restart=always
User=yc-user

[Install]
WantedBy=multi-user.target
EOF


# Активация
sudo systemctl daemon-reload
sudo systemctl enable x11 desktop
sudo systemctl start x11 desktop

echo 'export DISPLAY=:0' >> ~/.bashrc
export DISPLAY=:0
