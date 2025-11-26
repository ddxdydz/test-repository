import threading
from time import strftime

import pyautogui
import pygame

from basic.network.tools.time_ms import time_ms
from client.client_screen_receiver import ScreenReceiverClient


def process_screen_receiving():
    try:
        while True:
            start_receiving_event.wait()
            recv = client_screen_receiver.recv_screen()
            blit_data = {
                "screen_bytes": recv.pop("data").tobytes(),
                "cursor_x": recv.pop("cursor_x"),
                "cursor_y": recv.pop("cursor_y"),
                "metrics": recv
            }
            with blit_data_queue_lock:
                blit_data_queue.clear()
                blit_data_queue.append(blit_data)
    except Exception as ex:
        print(f"Pygame process_screen Error: {ex}")
        raise ex


def process_metrics_caption(
        index, size, screenshotted_time_ms, encoded_time_ms, received_time_ms, request_time_ms, decoded_time_ms,
        fps, last_blit_delay, blit_time_ms, last_screen_delay, last_basic_delay, last_tail
):
    encode_delay = encoded_time_ms - screenshotted_time_ms
    tail_delay = encoded_time_ms - request_time_ms
    network_delay = received_time_ms - encoded_time_ms
    decode_delay = decoded_time_ms - received_time_ms
    network_speed = round(size * 8 / 1024 / (network_delay / 1000), 3) if network_delay != 0 else "-"
    metrics_str_list = [
        f"{index} = {size} B",
        f"FPS: {int(fps)}",
        f"delay({last_screen_delay}): {str(time_ms() - screenshotted_time_ms).rjust(4, '0')} ms",
        # f"delay: {last_screen_delay} ms",
        f"blit_delay({last_blit_delay}): {str(time_ms() - blit_time_ms).rjust(4, '0')} ms",
        # f"blit_delay: {last_blit_delay} ms",
        f"basic_delay({last_basic_delay}): {decoded_time_ms - screenshotted_time_ms} ms",
        f"encode: {encode_delay} ms",
        f"network: {network_delay} ms",
        f"decode: {decode_delay} ms",
        f"tail({last_tail}): {tail_delay} ms",
        f"{network_speed}kbit/s",
        f"{strftime("%H:%M:%S")}"
    ]
    pygame.display.set_caption("   ".join(metrics_str_list))


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

    blit_time_ms = time_ms()
    current_raw_metrics["blit_time_ms"] = blit_time_ms
    current_raw_metrics["last_blit_delay"] = blit_time_ms - last_blit_time_ms
    current_raw_metrics["last_screen_delay"] = blit_time_ms - current_raw_metrics["screenshotted_time_ms"]
    current_raw_metrics["last_basic_delay"] = (
            current_raw_metrics["decoded_time_ms"] - current_raw_metrics["screenshotted_time_ms"])
    current_raw_metrics["last_tail"] = current_raw_metrics["encoded_time_ms"] - current_raw_metrics["request_time_ms"]
    current_raw_metrics.update(blit_data["metrics"])

    return blit_time_ms


def main():
    clock = pygame.time.Clock()
    running = True
    is_inactive = True
    blit_time_ms = time_ms()

    # client_command_sender.stop()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and is_inactive:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_inactive:
                    print(*pyautogui.position(), *pygame.mouse.get_pos(), sep=", ")
                if event.button == 2:
                    is_inactive = not is_inactive
                    if is_inactive:
                        start_receiving_event.clear()
                    else:
                        start_receiving_event.set()

        blit_time_ms = process_screen_blit(blit_time_ms)
        current_raw_metrics["fps"] = clock.get_fps()
        process_metrics_caption(**current_raw_metrics)
        pygame.display.flip()
        clock.tick(15)

    pygame.quit()


if __name__ == "__main__":
    pygame.init()
    client_screen_receiver = ScreenReceiverClient("158.160.202.50", 8888, 3, 80)
    try:
        client_screen_receiver.connect()

        SCREEN_SIZE = client_screen_receiver.get_screen_size()
        WINDOW_SIZE = (1200, 600) if SCREEN_SIZE[0] > 1400 or SCREEN_SIZE[1] > 1000 else SCREEN_SIZE

        blit_data_queue = []
        blit_data_queue_lock = threading.Lock()
        start_receiving_event = threading.Event()
        process_screen_thread = threading.Thread(target=process_screen_receiving, daemon=True)
        process_screen_thread.start()

        current_raw_metrics = {
            "index": 0, "size": 0, "screenshotted_time_ms": 0, "encoded_time_ms": 0, "request_time_ms": 0, "received_time_ms": 0, "decoded_time_ms": 0,
            "fps": 0, "last_blit_delay": 0, "blit_time_ms": 0, "last_screen_delay": 0, "last_basic_delay": 0, "last_tail": 0
        }

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
