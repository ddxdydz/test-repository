import threading
from enum import Enum
from typing import List

import pygame

from basic.network.tools.time_ms import time_ms
from client.client_screen_receiver import ScreenReceiverClient

FPS = 30
HOSTS = ['localhost', '158.160.182.121']
CURRENT_HOST = HOSTS[0]
PORTS = {"client_screen_receiver": 8888, "client_command_sender": 8888}
SCREEN_COLORS = 3
SCREEN_SCALE_PERCENT = 80


class State(Enum):
    INACTIVE = 0
    ONLY_COMMAND_SENDING = 1
    ACTIVE = 2

    def get_next_stage(self) -> Enum:
        return State((self.value + 1) % 3)


def get_metrics_str_list(index, screenshotted_time_ms, encoded_time_ms, received_time_ms, size) -> List[str]:
    encode_delay = encoded_time_ms - screenshotted_time_ms
    network_delay = received_time_ms - encoded_time_ms
    decode_delay = time_ms() - received_time_ms
    network_speed = round(size * 8 / 1024 / (network_delay / 1000), 3) if network_delay != 0 else "-"
    metrics_str_list = [
        f"{index} = {size} B",
        f"delay: {time_ms() - screenshotted_time_ms} ms",
        f"encode: {encode_delay} ms",
        f"network: {network_delay} ms",
        f"decode: {decode_delay} ms",
        f"{network_speed}kbit/s"
    ]
    return metrics_str_list


def process_screen_receiving():
    try:
        while True:
            start_receiving_event.wait()
            recv = client_screen_receiver.recv_screen()
            blit_data = {
                "screen_bytes": recv["data"].tobytes(),
                "metrics": {
                    "index": recv["index"],
                    "screenshotted_time_ms": recv["screenshotted_time_ms"],
                    "encoded_time_ms": recv["encoded_time_ms"],
                    "received_time_ms": recv["received_time_ms"],
                    "size": recv["size"]
                },
                "cursor_x": recv["cursor_x"],
                "cursor_y": recv["cursor_y"]
            }
            with blit_data_queue_lock:
                blit_data_queue.clear()
                blit_data_queue.append(blit_data)
    except Exception as ex:
        print(f"Pygame process_screen Error: {ex}")
        raise ex


def process_screen_blit(last_blit_time_ms: int) -> int:
    blit_data = None

    with blit_data_queue_lock:
        if blit_data_queue:
            blit_data = blit_data_queue[-1]
            blit_data_queue.clear()

    if blit_data is None:
        return last_blit_time_ms

    screen_to_blit = pygame.image.fromstring(blit_data["screen_bytes"], SCREEN_SIZE, 'RGB')
    screen.blit(screen_to_blit, (0, 0))
    cursor_x, cursor_y = blit_data["cursor_x"], blit_data["cursor_y"]
    pygame.draw.circle(screen, (255, 0, 0), (cursor_x, cursor_y), 5)
    pygame.draw.circle(screen, (255, 255, 255), (cursor_x, cursor_y), 2)

    current_blit_time_ms = time_ms()
    blit_delay = current_blit_time_ms - last_blit_time_ms
    blit_data["caption_metrics"].insert(1, f"blit_delay: {blit_delay} ms")

    pygame.display.set_caption("   ".join(blit_data["caption_metrics"]))

    return current_blit_time_ms


def process_current_state(current_state: State):
    if current_state == State.INACTIVE:
        pygame.display.set_caption(State.INACTIVE.name)
        start_receiving_event.clear()
    elif current_state == State.ONLY_COMMAND_SENDING:
        pygame.display.set_caption(State.ONLY_COMMAND_SENDING.name)
        start_receiving_event.clear()
    else:
        start_receiving_event.set()


def main():
    clock = pygame.time.Clock()
    running = True
    current_state = State.INACTIVE
    blit_time_ms = time_ms()

    # client_command_sender.stop()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and current_state == State.INACTIVE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:  # колесо
                    # client_command_sender.reset_calibration(*pygame.mouse.get_pos())
                    current_state = current_state.get_next_stage()

        blit_time_ms = process_screen_blit(blit_time_ms)
        process_current_state(current_state)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    pygame.init()
    client_screen_receiver = ScreenReceiverClient(
        CURRENT_HOST, PORTS["client_screen_receiver"], SCREEN_COLORS, SCREEN_SCALE_PERCENT
    )
    try:
        client_screen_receiver.connect()

        SCREEN_SIZE = client_screen_receiver.get_screen_size()
        WINDOW_SIZE = (800, 400) if SCREEN_SIZE[0] > 1400 or SCREEN_SIZE[1] > 1000 else SCREEN_SIZE

        blit_data_queue = []
        blit_data_queue_lock = threading.Lock()
        start_receiving_event = threading.Event()
        process_screen_thread = threading.Thread(target=process_screen_receiving, daemon=True)
        process_screen_thread.start()

        screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        main()
    except Exception as e:
        print(f"Pygame Error: {e}")
        raise e
    finally:
        client_screen_receiver.close()
        print("client_screen_receiver closed.")


# if current_state != State.INACTIVE and not client_command_sender.is_recording:
#     client_command_sender.start()
# if current_state == State.INACTIVE and client_command_sender.is_recording:
#     client_command_sender.stop()
# client_command_sender = CommandRecorderClient(current_host, port_2)
# client_command_sender.SCREEN_SIZE[0], client_command_sender.SCREEN_SIZE[1] = SCREEN_SIZE
# client_command_sender.connect()
# client_command_sender.close()
# print("client_command_sender closed.")
