cat > ~/hello.py << 'EOF'
print("hello from python")
EOF
chmod +x ~/hello.py

cat > ~/test_imports.py << 'EOF'
try:
    import numpy as np
    import pyautogui
    from PIL import Image
    print("Все библиотеки успешно импортированы!")
    print(pyautogui.size())
except ImportError as e:
    print(f"Ошибка импорта: {e}")
EOF
chmod +x ~/test_imports.py


cat > ~/chromium_check.sh << 'EOF'
systemctl --user list-units | grep chromium-browser
EOF
chmod +x ~/chromium_check.sh

cat > ~/chromium_start.sh << 'EOF'
systemd-run --user --slice=snap.slice --setenv=DISPLAY=:0 chromium-browser
EOF
chmod +x ~/chromium_start.sh

cat > ~/server_s.sh << 'EOF'
PYTHONPATH=/home/yc-user/test-repository python3 ~/test-repository/server/server_screen_sender.py
EOF
chmod +x ~/server_s.sh

cat > ~/server_c.sh << 'EOF'
PYTHONPATH=/home/yc-user/test-repository python3 ~/test-repository/server/server_command_receiver.py
EOF
chmod +x ~/server_c.sh


# Для буфера обмена
sudo apt install xclip

cat << 'EOF' > ~/c
#!/bin/bash
echo "Введите текст (Ctrl+D для завершения ввода):"
# Читаем весь ввод до Ctrl+D
input_text=$(cat)
# Копируем в буфер обмена
echo -n "$input_text" | xclip -selection clipboard
echo ""
echo "Текст скопирован в буфер обмена!"
EOF
chmod +x ~/c

tee ~/v > /dev/null << EOF
#!/bin/bash
xclip -selection clipboard -o
echo ""
EOF
chmod +x ~/v
