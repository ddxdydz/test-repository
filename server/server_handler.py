import socket
from enum import Enum

import pyautogui

from support.Key import Key
from support.Server import Server
from support.tools import recv_all


class Action(Enum):  # 16 действий максимум
    ON_MOVE = 1
    ON_CLICK_RELEASED_LEFT = 2
    ON_CLICK_RELEASED_RIGHT = 3
    ON_CLICK_PRESSED_LEFT = 4
    ON_CLICK_PRESSED_RIGHT = 5
    ON_SCROLL = 6
    ON_PRESS_REGULAR = 7
    ON_PRESS_SPECIAL = 8
    ON_RELEASE_REGULAR = 9
    ON_RELEASE_SPECIAL = 10


class CommandHandler:
    def __init__(self, input_socket: socket.socket, active=False):
        self.socket = input_socket
        self.active = active

    def recv_command(self) -> bool:
        try:
            command_data = recv_all(self.socket, size=4, chunk_size=16)
            if len(command_data) != 4:
                print(f"CommandHandler: len(command_data) = {len(command_data)} != 4")
                return False
            command_int = int.from_bytes(command_data[:4], byteorder='big', signed=False)
            # Разбираем битовые поля:
            action = Action((command_int >> 28) & 0b1111)  # первые 4 бита - action, биты 28-31 (4 бита)
            val1 = (command_int >> 14) & 0b11111111111111  # следующие 14 битов - val1, биты 14-27 (14 бит)
            val2 = command_int & 0b11111111111111  # оставшиеся 14 битов - val2, биты 0-13 (14 бит)

            if self.active:
                self.process_command(action, val1, val2)
            else:
                print("command", action, val1, val2)
            return True

        except ValueError as e:
            print(f"Ошибка парсинга команды: {e}")
            return False
        except ConnectionResetError:
            print("Клиент принудительно разорвал соединение")
            return False
        except ConnectionAbortedError:
            print("Соединение было разорвано")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return False

    @staticmethod
    def check_range(x, y):
        width, height = pyautogui.size()
        if 0 < x < width:
            if 0 < y < height:
                return True
        return False

    @staticmethod
    def process_command(action: Action, val1: int, val2: int) -> bool:
        try:
            if action == Action.ON_MOVE and CommandHandler.check_range(val1, val2):
                pyautogui.moveTo(val1, val2)
                print("processed", action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_RELEASED_LEFT and CommandHandler.check_range(val1, val2):
                pyautogui.mouseUp(val1, val2, button='left')
                print("processed", action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_RELEASED_RIGHT and CommandHandler.check_range(val1, val2):
                pyautogui.mouseUp(val1, val2, button='right')
                print("processed", action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_PRESSED_LEFT and CommandHandler.check_range(val1, val2):
                pyautogui.mouseDown(val1, val2, button='left')
                print("processed", action, (val1, val2), pyautogui.position())
            elif action == Action.ON_CLICK_PRESSED_RIGHT and CommandHandler.check_range(val1, val2):
                pyautogui.mouseDown(val1, val2, button='right')
                print("processed", action, (val1, val2), pyautogui.position())
            elif action == Action.ON_SCROLL:
                pyautogui.hscroll(val1 - 1)
                pyautogui.vscroll(val2 - 1)
                print("processed", action, (val1 - 1, val2 - 1), pyautogui.position())
            elif action == Action.ON_PRESS_REGULAR:
                key_name = chr(val1)
                pyautogui.keyDown(key_name)
                print("process", action, (val1, val2), key_name)
            elif action == Action.ON_PRESS_SPECIAL:
                key_name = Key(val1).name
                pyautogui.keyDown(key_name)
                print("process", action, (val1, val2), key_name)
            elif action == Action.ON_RELEASE_REGULAR:
                key_name = chr(val1)
                pyautogui.keyUp(key_name)
                print("process", action, (val1, val2), key_name)
            elif action == Action.ON_RELEASE_SPECIAL:
                key_name = Key(val1).name
                pyautogui.keyUp(key_name)
                print("process", action, (val1, val2), key_name)
            else:
                if CommandHandler.check_range(val1, val2):
                    print(f"Неизвестное действие: {action}")
                else:
                    print(f"Проверте диапазан x:{val1} y:{val2}.")
                return False
            return True
        except Exception as e:
            print(f"Ошибка выполнения команды: {str(e)}")
            return False


class CommandHandlerServer(Server):
    def __init__(self, host='0.0.0.0', port=0):
        super().__init__(host, port)

    def client_loop(self, client_socket, address):
        command_handler = CommandHandler(client_socket, False)
        print("CommandHandlerServer: start client_loop.")
        while self.running:
            try:
                # Если recv_command возвращает False, клиент отключился
                if not command_handler.recv_command():
                    break
            except Exception as e:
                print(f"Error (CommandHandlerServer, client_loop): {e}")
                break
        print("CommandHandlerServer: end client_loop.")


if __name__ == "__main__":
    server = CommandHandlerServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Остановка сервера...")
        server.stop()
