import socket
from collections.abc import Buffer
from typing import Any


class SocketTransceiverError(Exception):
    """Базовое исключение для ошибок сокета"""
    pass


class TerminatedSocketTransceiverError(SocketTransceiverError):
    """Исключение при обрыве соединения"""
    pass


class TimeoutSocketTransceiverError(SocketTransceiverError):
    """Исключение при таймауте операции"""
    pass


class SocketTransceiver:
    """
    Класс для надежной отправки и получения данных через сокет.

    Поддерживает два режима работы:
    1. Сырой режим (raw): данные передаются как есть, без метаданных
    2. Режим с фреймингом (framed): данные предваряются заголовком с размером header_size

    Режим с фреймингом гарантирует, что полные сообщения будут получены независимо
    от фрагментации в сети.

    Атрибуты:
        socket (socket.socket): Базовый объект сокета
        header_size (int): Размер заголовка в байтах для хранения размера данных
        max_payload_size (int): Максимальный допустимый размер данных в режиме с фреймингом
        receive_chunk_size (int): Размер чанков для приема больших сообщений
    """

    def __init__(self, sock: socket.socket, header_size: int = 4):
        """
        Инициализирует трансмиттер сокета.

        Args:
            sock: Сокет для отправки и получения данных
            header_size: Размер заголовка в байтах (по умолчанию 4 = 4GB)

        Raises:
            ValueError: Если header_size меньше 1
        """
        self.name = self.__class__.__name__

        if header_size < 1:
            raise ValueError(f"{self.name}: Header size must be positive, got {header_size}")

        self._socket = sock
        self.receive_chunk_size = 4096
        self.header_size = header_size
        self.max_payload_size = (256 ** header_size) - 1  # e.g., 4GB for 4 bytes

    def _validate_size(self, size: int) -> None:
        """Проверяет, что размер данных находится в допустимых пределах."""
        if not isinstance(size, int):
            raise TypeError(f"{self.name}: Size must be integer, got {type(size)}")
        if size < 0:
            raise ValueError(f"{self.name}: Size cannot be negative, got {size}")
        if size > self.max_payload_size:
            raise ValueError(f"{self.name}: Size {size} exceeds maximum allowed size {self.max_payload_size}")

    def _validate_data(self, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError(f"{self.name}: Data must be bytes, got {type(data)}")
        if not data:
            raise ValueError(f"{self.name}: Data cannot be empty")

    def _recv_all(self, num_bytes: int) -> bytes:
        """
        Получает точно указанное количество байт из сокета.

        Гарантирует, что будет получено ровно num_bytes байт, даже если данные
        приходят частями из-за фрагментации сети.

        Args:
            num_bytes: Точное количество байт для получения

        Returns:
            bytes: Полученные данные

        Raises:
            TerminatedSocketTransceiverError: Если соединение закрыто или запрошено 0 байт
            TimeoutSocketTransceiverError: Если превышен таймаут при получении данных
        """
        if self.closed:
            raise TerminatedSocketTransceiverError(f"Socket is closed")

        if num_bytes == 0:
            raise TerminatedSocketTransceiverError("Input zero bytes to receive")

        self._validate_size(num_bytes)

        data_chunks = []
        received_bytes = 0

        while received_bytes < num_bytes:
            remaining_bytes = num_bytes - received_bytes
            chunk_size = min(self.receive_chunk_size, remaining_bytes)

            try:
                chunk = self._socket.recv(chunk_size)
            except socket.timeout:
                raise TimeoutSocketTransceiverError(
                    f"Timeout while receiving data ({received_bytes}/{num_bytes} bytes received)"
                )

            if not chunk:
                raise TerminatedSocketTransceiverError(
                    f"Connection closed while receiving data ({received_bytes}/{num_bytes} bytes received)"
                )

            data_chunks.append(chunk)
            received_bytes += len(chunk)

        return b''.join(data_chunks)

    def recv_raw(self, num_bytes: int) -> bytes:
        """Получает ровно num_bytes байт в сыром режиме."""
        return self._recv_all(num_bytes)

    def recv_framed(self) -> bytes:
        """Получает одно сообщение в режиме с фреймингом."""
        size_bytes = self._recv_all(self.header_size)
        size = int.from_bytes(size_bytes, 'big', signed=False)
        return self._recv_all(size)

    def _send_all(self, data: bytes):
        if self.closed:
            raise TerminatedSocketTransceiverError(f"Socket is closed")

        self._validate_data(data)

        total_sent = 0
        data_length = len(data)

        while total_sent < data_length:

            try:
                sent = self._socket.send(data[total_sent:])
            except socket.timeout:
                raise TimeoutSocketTransceiverError(
                    f"Timeout while sending data ({total_sent}/{data_length} bytes sent)"
                )

            if sent == 0:
                raise TerminatedSocketTransceiverError(
                    f"Connection closed while sending data ({total_sent}/{data_length} bytes sent)"
                )

            total_sent += sent
        return total_sent

    def send_raw(self, data: bytes) -> None:
        """Данные в сыром режиме."""
        size = len(data)
        self._validate_size(size)
        self._send_all(data)

    def send_framed(self, data: bytes) -> None:
        """Отправляет данные в режиме с фреймингом."""
        size = len(data)
        self._validate_size(size)
        size_bytes = size.to_bytes(self.header_size, 'big', signed=False)
        self._send_all(size_bytes + data)

    def set_timeout(self, timeout: float | None):
        """Устанавливает таймаут для операций с сокетом в секундах."""
        if self._socket:
            self._socket.settimeout(timeout)

    def connect(self, __address: tuple[Any, ...] | str | Buffer | Buffer) -> None:
        self._socket.connect(__address)

    def close(self):
        """Закрывает базовый сокет."""
        if self._socket:
            self._socket.close()

    @property
    def closed(self) -> bool:
        """Проверяет, закрыт ли сокет."""
        return self._socket is None or self._socket.fileno() == -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
