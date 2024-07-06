"""Exeptions."""


class Error(Exception):
    """Базовый класс."""

    pass


class ApiError(Error):
    """Ошибка доступа к эндпоинту."""

    def __init__(self, message='Не удалось получить доступ к API.'):
        """Возвращает ApiError."""
        self.message = message
        super().__init__(self.message)
