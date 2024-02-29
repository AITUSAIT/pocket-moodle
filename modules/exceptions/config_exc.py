from typing import Any


class BaseException(Exception):
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class ConfigFieldIsRequired(BaseException):
    def __init__(self, config_field: str) -> None:
        self.message = f"Config field `{config_field}` is required! Specify in .env"
        super().__init__()


class ConfigFieldWrongType(BaseException):
    def __init__(self, config_field: str, value: Any, needed_type: type[Any]) -> None:
        self.message = f"Config field {config_field} must be {needed_type}! Check .env!\n{config_field}={value}"
        super().__init__()
