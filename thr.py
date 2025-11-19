import threading
import time

stop_event = threading.Event()


def worker():
    print("Рабочий поток: начал работу")
    while not stop_event.is_set():
        print("Рабочий поток: работаю...")
        time.sleep(1)

    # Корректное завершение
    print("Рабочий поток: завершаю работу, освобождаю ресурсы")
    # Закрываем файлы, соединения и т.д.


thread = threading.Thread(target=worker)
thread.start()

# Ждем 5 секунд
time.sleep(5)

print("Останавливаю поток...")
stop_event.set()
thread.join()