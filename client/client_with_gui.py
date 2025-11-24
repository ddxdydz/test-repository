import threading
from enum import Enum
from time import time

import pygame

from basic.network.time_ms import time_ms
from client.client_screen_receiver import ScreenReceiverClient


class State(Enum):
    INACTIVE = 0
    ONLY_HANDLER = 1
    ACTIVE = 2

    def get_next_stage(self) -> Enum:
        return State((self.value + 1) % 3)


def get_metrics_str(screen_index, weight, screen_time_in_ms, start_sending_time_in_ms, received_time_in_ms) -> str:
    server_delay = start_sending_time_in_ms - screen_time_in_ms
    network_delay = received_time_in_ms - start_sending_time_in_ms
    decode_delay = time_ms() - received_time_in_ms
    current_speed = round(weight * 8 / 1024 / (network_delay / 1000), 3) if network_delay != 0 else "-"
    str_metrics = [
        f"{screen_index} = {weight} B",
        f"delay: {time_ms() - screen_time_in_ms} ms",
        f"encode: {server_delay} ms",
        f"network: {network_delay} ms",
        f"decode: {decode_delay} ms",
        f"{current_speed}kbit/s"
    ]
    return '    '.join(str_metrics)


def process_receiving():
    try:
        while True:
            continue_receiving_event.wait()
            recv = client_screen_receiver.recv_screen()
            receiving_data_to_blit = {
                "screen_bytes": recv["image_array"].tobytes(),
                "caption": get_metrics_str(
                    recv["screen_index"], recv["weight"], recv["screen_time_in_ms"],
                    recv["start_sending_time_in_ms"], recv["received_time_in_ms"]),
                "cursor_x": recv["cursor_x"],
                "cursor_y": recv["cursor_y"]
            }
            with receiving_data_queue_lock:
                receiving_data_queue.clear()
                receiving_data_queue.append(receiving_data_to_blit)
    except Exception as ex:
        print(f"Pygame process_screen Error: {ex}")
        raise ex


def process_blit():
    receiving_data_to_blit = None
    with receiving_data_queue_lock:
        if receiving_data_queue:
            receiving_data_to_blit = receiving_data_queue[-1]
            receiving_data_queue.clear()
    if receiving_data_to_blit is not None:
        screen_to_blit = pygame.image.fromstring(receiving_data_to_blit["screen_bytes"], SCREEN_SIZE, 'RGB')
        screen.blit(screen_to_blit, (0, 0))
        cursor_x, cursor_y = receiving_data_to_blit["cursor_x"], receiving_data_to_blit["cursor_y"]
        pygame.draw.circle(screen, (0, 0, 255), (cursor_x, cursor_y), 4)
        pygame.draw.circle(screen, (255, 255, 255), (cursor_x, cursor_y), 2)
        pygame.display.set_caption(receiving_data_to_blit["caption"])


def process_current_state(current_state: State):
    if current_state == State.INACTIVE:
        pygame.display.set_caption(State.INACTIVE.name)
        continue_receiving_event.clear()
    elif current_state == State.ONLY_HANDLER:
        pygame.display.set_caption(State.ONLY_HANDLER.name)
        continue_receiving_event.clear()
    else:
        continue_receiving_event.set()
    # if current_state != State.INACTIVE and not client_command_sender.is_recording:
    #     client_command_sender.start()
    # if current_state == State.INACTIVE and client_command_sender.is_recording:
    #     client_command_sender.stop()


def main():
    clock = pygame.time.Clock()
    running = True
    current_state = State.INACTIVE

    # client_command_sender.stop()

    while running:
        _start_loop = time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_state == State.INACTIVE:
                        running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:  # колесо
                    # client_command_sender.reset_calibration(*pygame.mouse.get_pos())
                    current_state = current_state.get_next_stage()

        process_blit()
        process_current_state(current_state)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("MY PYGAME")
    FPS = 30

    HOSTS = ['localhost', '158.160.182.121', ]
    PORTS = [2952, 8888]
    client_screen_receiver = ScreenReceiverClient(HOSTS[0], PORTS[0], 4, 80)
    # client_command_sender = CommandRecorderClient(current_host, port_2)

    try:
        client_screen_receiver.connect()
        SCREEN_SIZE = client_screen_receiver.get_screen_size()
        # client_command_sender.SCREEN_SIZE[0], client_command_sender.SCREEN_SIZE[1] = SCREEN_SIZE
        # client_command_sender.connect()
        WINDOW_SIZE = (1000, 800) if SCREEN_SIZE[0] > 1400 or SCREEN_SIZE[1] > 1000 else SCREEN_SIZE
        screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)

        continue_receiving_event = threading.Event()
        receiving_data_queue_lock = threading.Lock()
        receiving_data_queue = []
        process_screen_thread = threading.Thread(target=process_receiving, daemon=True)
        process_screen_thread.start()

        main()
    except Exception as e:
        print(f"Pygame Error: {e}")
    finally:
        client_screen_receiver.close()
        print("client_screen_receiver closed.")
        # client_command_sender.close()
        # print("client_command_sender closed.")
