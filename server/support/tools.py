import socket

MAX_SIZE = 100 * 1024 * 1024


def recv_all(sock: socket.socket, size: int, chunk_size: int = 4096,
             max_size: int = MAX_SIZE) -> bytes:
    if size < 0 or size > max_size:
        raise ValueError("tools/recvall: size < 1")
    if chunk_size < 8:
        raise ValueError("tools/recvall: chunk_size < 8")
    try:
        data = []
        received = 0
        while received < size:
            remaining = size - received
            chunk = sock.recv(min(chunk_size, remaining))
            if not chunk:
                print(f"tools/recvall: not chunk")
                return b''
            data.append(chunk)
            received += len(chunk)
        if received != size:
            print("tools/recvall: data_received != size")
            return b''
        return b"".join(data)
    except Exception as e:
        print(f"tools/recvall: Error: {e}")
        return b''


def send_with_header_size(sock: socket.socket, data: bytes, header_size: int = 4,
                          max_size: int = MAX_SIZE,) -> bool:
    """
    Отправка данных с проверкой размера и таймаутом, Возвращает True в случае успешной отправки
    """
    data_size = len(data)
    if data_size < 1:  # Должен быть передан как минимум один байт
        raise ValueError("tools/send_with_header_size: data_size < 1")
    if data_size > max_size:  # Проверка размера
        raise ValueError("tools/send_with_header_size: data_size > max_size")
    if header_size not in (1, 2, 4, 8):  # Проверка header_size
        raise ValueError("tools/send_with_header_size: header_size not in (1, 2, 4, 8)")
    max_possible_size = (1 << (header_size * 8)) - 1
    if data_size > max_possible_size:  # Проверяем, что размер помещается в header_size
        raise ValueError("tools/send_with_header_size: data_size > max_possible_size")
    try:
        size = data_size.to_bytes(header_size, 'big', signed=False)
        sock.sendall(size + data)
        return True
    except Exception as e:
        print(f"tools/send_with_header_size: Error: {e}")
        return False


def recv_with_header_size(sock: socket.socket, chunk_size: int = 4096, header_size: int = 4,
                          max_size: int = MAX_SIZE) -> bytes:
    # Получаем заголовок с размером
    size_data = recv_all(sock, header_size, chunk_size, max_size)

    if not size_data:
        print("tools/recv_with_header_size: not success")
        return b''

    try:
        size = int.from_bytes(size_data, 'big', signed=False)
    except (ValueError, OverflowError):
        print(f"tools/recv_with_header_size: size is not parsed chunk_size{chunk_size}, header_size{header_size}")
        return b''

    if size < 0 or size > max_size:  # Защита от нереальных размеров
        raise ValueError(f"tools/recv_with_header_size: size < 0 or size > max_size (size)")

    return recv_all(sock, size, chunk_size, max_size)
