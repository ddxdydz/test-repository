python3 -c "
import pyautogui
screenshot = pyautogui.screenshot()
print(f'Скриншот: {screenshot.size}')
screenshot.save('./test.png')
print('Сохранен: ./test.png')
"
convert test.bmp test2.png
echo "http://$(curl -s ifconfig.me):8088/test2.png"
python3 -m http.server 8088
