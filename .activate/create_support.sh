#!/bin/bash

cat > ~/py-hello.py << 'EOF'
print("hello from python")
EOF
chmod +x ~/py-hello.py

cat > ~/py-imports.py << 'EOF'
try:
    import numpy as np
    import pyautogui
    from PIL import Image
    print("Все библиотеки успешно импортированы!")
    print(pyautogui.size())
except ImportError as e:
    print(f"Ошибка импорта: {e}")
EOF
chmod +x ~/py-imports.py

cat > ~/chrome-check << 'EOF'
systemctl --user list-units | grep chromium-browser
EOF
chmod +x ~/chrome-check

cat > ~/chrome-start << 'EOF'
systemd-run --user --slice=snap.slice --setenv=DISPLAY=:0 chromium-browser
EOF
chmod +x ~/chrome-start

cat > ~/sscreen << 'EOF'
python3 ~/test-repository/server_screen_sender.py
EOF
chmod +x ~/sscreen

cat > ~/scommand << 'EOF'
python3 ~/test-repository/server_command_receiver.py
EOF
chmod +x ~/scommand


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

tee ~/encrypt > /dev/null << EOF
python ~/test-repository/basic/crypt/encrypt.py ~/Downloads
EOF
chmod +x ~/encrypt
