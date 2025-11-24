from enum import Enum
from time import time

import pygame

from client.client_screen_receiver import ScreenReceiverClient


class State(Enum):
    INACTIVE = 0
    ONLY_HANDLER = 1
    ACTIVE = 2

    def get_next_stage(self) -> Enum:
        return State((self.value + 1) % 3)


def show_info(loop_time_in_s, screen_index, weight,
              screen_time_in_ms, send_request_time_in_ms, start_sending_time_in_ms,  received_time_in_ms, **kwargs):
    fps = round(1 / loop_time_in_s, 3)

    request_delay = send_request_time_in_ms - screen_time_in_ms
    server_delay = start_sending_time_in_ms - send_request_time_in_ms
    network_delay = received_time_in_ms - start_sending_time_in_ms
    decode_delay = int(time() * 1000) - received_time_in_ms
    current_speed = round(weight * 8 / 1024 / (network_delay / 1000), 3)

    str_metrics = [
        f"{screen_index} = {weight} B",
        f"FPS: {fps}",
        f"delay: {int(time() * 1000) - screen_time_in_ms} ms",
        f"blit: {int(loop_time_in_s * 1000)} ms",
        f"request: {request_delay} ms",
        f"server: {server_delay} ms",
        f"network: {network_delay} ms",
        f"decode: {decode_delay} ms",
        f"{current_speed}кбит/с"
    ]

    pygame.display.set_caption('    '.join(str_metrics))


def main():
    clock = pygame.time.Clock()
    running = True
    current_state = State.INACTIVE

    # client_command_sender.stop()

    while running:
        start_loop_time = time()
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

        if current_state == State.INACTIVE:
            pygame.display.set_caption(State.INACTIVE.name)
        elif current_state == State.ONLY_HANDLER:
            pygame.display.set_caption(State.ONLY_HANDLER.name)
        else:
            try:
                received = client_screen_receiver.recv_screen()
                screen_to_blit = pygame.image.fromstring(received["image_array"].tobytes(), SCREEN_SIZE, 'RGB')
                screen.blit(screen_to_blit, (0, 0))
                pygame.draw.circle(screen, (255, 255, 255), (received["cursor_x"], received["cursor_y"]), 5)
                pygame.draw.circle(screen, (0, 0, 255), (received["cursor_x"], received["cursor_y"]), 3)
                show_info(time() - start_loop_time, **received)
            except Exception as exp:
                print(f"Pygame LOOP screen blit Error: {exp}")

        # if current_state != State.INACTIVE and not client_command_sender.is_recording:
        #     client_command_sender.start()
        # if current_state == State.INACTIVE and client_command_sender.is_recording:
        #     client_command_sender.stop()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    client_screen_receiver, client_command_sender = None, None
    try:
        pygame.init()
        pygame.display.set_caption("MY PYGAME")
        FPS = 20

        vm = '158.160.182.121'
        lh = 'localhost'
        current_host = lh
        port_1, port_2 = 48693, 50589

        client_screen_receiver = ScreenReceiverClient(current_host, port_1, 4, 80)
        client_screen_receiver.connect()
        SCREEN_SIZE = client_screen_receiver.get_screen_size()

        # client_command_sender = CommandRecorderClient(current_host, port_2)
        # client_command_sender.SCREEN_SIZE[0], client_command_sender.SCREEN_SIZE[1] = SCREEN_SIZE
        # client_command_sender.connect()

        WINDOW_SIZE = (SCREEN_SIZE[0] // 2 if SCREEN_SIZE[0] > 1400 else SCREEN_SIZE[0],
                       SCREEN_SIZE[1] // 2 if SCREEN_SIZE[1] > 1000 else SCREEN_SIZE[1])
        screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        main()
    except Exception as e:
        print(f"Pygame Error: {e}")
    finally:
        if client_screen_receiver is not None:
            client_screen_receiver.close()
            print("client_screen_receiver closed.")
        if client_command_sender is not None:
            client_command_sender.close()
            print("client_command_sender closed.")
