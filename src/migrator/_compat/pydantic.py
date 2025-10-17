"""Lightweight subset of Pydantic used as an offline fallback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, get_args, get_origin, get_type_hints


_T = TypeVar("_T", bound="BaseModel")


@dataclass
class FieldInfo:
    default: Any
    alias: Optional[str] = None
    description: Optional[str] = None


def Field(default: Any, *, alias: Optional[str] = None, description: Optional[str] = None) -> FieldInfo:
    """Emulate :func:`pydantic.Field` for simple use-cases."""

    return FieldInfo(default=default, alias=alias, description=description)


class BaseModel:
    """Minimal drop-in replacement for :class:`pydantic.BaseModel`."""

    __field_defaults__: Dict[str, Tuple[Any, Optional[str]]]
    __field_types__: Dict[str, Any]

    def __init_subclass__(cls) -> None:  # pragma: no cover - behaviour validated indirectly
        cls.__field_defaults__ = {}
        cls.__field_types__ = get_type_hints(cls)
        for name, annotation in cls.__field_types__.items():
            attr = getattr(cls, name, None)
            if isinstance(attr, FieldInfo):
                default = attr.default
                alias = attr.alias or name
                cls.__field_defaults__[name] = (default, alias)
                if default is ...:
                    setattr(cls, name, None)
                else:
                    setattr(cls, name, default)
            else:
                cls.__field_defaults__[name] = (attr, name)

    def __init__(self, **data: Any) -> None:
        for name, annotation in self.__field_types__.items():
            default, alias = self.__field_defaults__.get(name, (None, name))
            key = alias or name
            if key in data:
                raw_value = data[key]
            elif name in data:
                raw_value = data[name]
            else:
                if default is ...:
                    raise ValueError(f"Missing required field {name}")
                raw_value = default
            value = self._convert(annotation, raw_value)
            setattr(self, name, value)

    @classmethod
    def parse_obj(cls: Type[_T], obj: Any) -> _T:
        if isinstance(obj, cls):
            return obj
        if not isinstance(obj, dict):
            raise TypeError("parse_obj expects a dictionary")
        return cls(**obj)

    def dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for name in self.__field_types__:
            value = getattr(self, name)
            result[name] = self._serialize(value)
        return result

    def json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.dict(), indent=indent)

    @classmethod
    def _convert(cls, annotation: Any, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation.parse_obj(value)
        origin = get_origin(annotation)
        if origin in (list, List):
            item_type = get_args(annotation)[0]
            return [cls._convert(item_type, item) for item in (value or [])]
        if origin in (tuple, Tuple):
            item_type = get_args(annotation)[0]
            return tuple(cls._convert(item_type, item) for item in value)
        if origin in (dict, Dict):
            key_type, val_type = get_args(annotation)
            return {cls._convert(key_type, k): cls._convert(val_type, v) for k, v in value.items()}
        if origin is Optional:
            sub_type = get_args(annotation)[0]
            return cls._convert(sub_type, value)
        return value

    @classmethod
    def _serialize(cls, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.dict()
        if isinstance(value, list):
            return [cls._serialize(item) for item in value]
        return value


__all__ = ["BaseModel", "Field"]
