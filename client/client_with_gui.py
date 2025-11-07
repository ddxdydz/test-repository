from enum import Enum
from time import time

import pygame

from client.client_command_sender import CommandRecorderClient
from client.client_screen_receiver import ScreenReceiverClient


class State(Enum):
    INACTIVE = 0
    ONLY_HANDLER = 1
    ACTIVE = 2

    def get_next_stage(self) -> Enum:
        return State((self.value + 1) % 3)


def show_info(start_loop_time, weight, screen_blit_count, width, height):
    fps = 1 / (time() - start_loop_time)
    current_fps = round(fps, 3)
    current_weight = weight // 1024
    current_speed = round(fps * current_weight * 8, 3)
    pygame.display.set_caption(
        f"{screen_blit_count}    " +
        f"{width}x{height}    " +
        f"FPS: {current_fps}    " +
        f"{current_weight}KB"    " + "
        f"{current_speed}кбит/с"
    )


def main():
    clock = pygame.time.Clock()
    running = True
    current_state = State.INACTIVE

    screen_blit_count = 0

    while running:
        start_loop_time = time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                print(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:
                    client_command_sender.reset_calibration(*pygame.mouse.get_pos())
                    current_state = current_state.get_next_stage()

        if current_state == State.INACTIVE:
            pygame.display.set_caption(State.INACTIVE.name)
        elif current_state == State.ONLY_HANDLER:
            pygame.display.set_caption(State.ONLY_HANDLER.name)
        else:
            try:
                size, image_bytes = client_screen_receiver.recv_screen_bytes()
                sc = pygame.image.fromstring(image_bytes, SERVER_SCREEN_SIZE, 'RGB')
                screen.blit(sc, (0, 0))
                screen_blit_count += 1
                show_info(start_loop_time, size, screen_blit_count, *client_screen_receiver.get_screen_size())
            except Exception as exp:
                print(f"Pygame LOOP screen blit Error: {exp}")

        if current_state != State.INACTIVE and not client_command_sender.is_recording:
            client_command_sender.start()
        if current_state == State.INACTIVE and client_command_sender.is_recording:
            client_command_sender.stop()

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
        current_host = vm
        port_1, port_2 = 45571, 45743

        client_screen_receiver = ScreenReceiverClient(current_host, port_1)
        client_screen_receiver.connect()
        client_screen_receiver.start()
        SERVER_SCREEN_SIZE = client_screen_receiver.get_screen_size()

        client_command_sender = CommandRecorderClient(current_host, port_2)
        client_command_sender.SCREEN_SIZE[0], client_command_sender.SCREEN_SIZE[1] = SERVER_SCREEN_SIZE
        client_command_sender.connect()

        WINDOW_SIZE = (
            SERVER_SCREEN_SIZE[0] // 2 if SERVER_SCREEN_SIZE[0] > 1400 else SERVER_SCREEN_SIZE[0],
            SERVER_SCREEN_SIZE[1] // 2 if SERVER_SCREEN_SIZE[1] > 1000 else SERVER_SCREEN_SIZE[1]
        )
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
