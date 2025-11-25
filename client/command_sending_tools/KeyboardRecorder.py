from pynput import keyboard
from pynput.keyboard import KeyCode, Key

from basic.network.actions_transfer.Action import Action
from basic.network.actions_transfer.key_maps import KEY_MAP_NAME_TO_NUM
from client.command_sending_tools.CommandSender import CommandSender


class KeyboardRecorder:
    @staticmethod
    def on_press(key: (Key | KeyCode | None)) -> None:
        try:
            if hasattr(key, 'char') and key.char is not None:
                CommandSender.send_command(Action.ON_PRESS_REGULAR, ord(key.char), 0)
            elif key == Key.space:
                CommandSender.send_command(Action.ON_PRESS_REGULAR, ord(' '), 0)
            elif isinstance(key, Key):
                CommandSender.send_command(Action.ON_PRESS_SPECIAL, KEY_MAP_NAME_TO_NUM[key.name], 2)
        except Exception as e:
            print(f"Error in on_press: {e}")

    @staticmethod
    def on_release(key: (Key | KeyCode | None)) -> None:
        try:
            if hasattr(key, 'char') and key.char is not None:
                CommandSender.send_command(Action.ON_RELEASE_REGULAR, ord(key.char), 0)
            elif key == Key.space:
                CommandSender.send_command(Action.ON_RELEASE_REGULAR, ord(' '), 0)
            elif isinstance(key, Key):
                CommandSender.send_command(Action.ON_RELEASE_SPECIAL, KEY_MAP_NAME_TO_NUM[key.name], 2)
        except Exception as e:
            print(f"Error in on_release: {e}")


if __name__ == "__main__":
    keyboard_listener = keyboard.Listener(
        on_press=KeyboardRecorder.on_press,
        on_release=KeyboardRecorder.on_release,
        suppress=False
    )
    keyboard_listener.start()
    while True:
        pass
