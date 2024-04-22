import os
from typing import Any

from modules.utils.exceptions import ConfigFieldIsRequired, ConfigFieldWrongType


def get_from_env(field: str, default: Any | None = None, value_type: type[str | int | Any] = str) -> int | str | Any:
    value = os.getenv(field, default)
    if value is None and default is None:
        raise ConfigFieldIsRequired(field)

    if not isinstance(value, value_type):
        if isinstance(value, str) and value_type is int:
            try:
                return int(value)
            except Exception:
                raise ConfigFieldWrongType(field, value, value_type)  # pylint: disable=raise-missing-from
        raise ConfigFieldWrongType(field, value, value_type)

    return value
