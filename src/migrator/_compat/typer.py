"""Minimal Typer-compatible API for offline environments."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, get_args, get_origin, get_type_hints


class Exit(Exception):
    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = code


class BadParameter(Exception):
    """Raised when a CLI parameter is invalid."""


@dataclass
class OptionInfo:
    default: Any
    names: Tuple[str, ...]
    help: Optional[str] = None


def Option(default: Any, *names: str, help: str | None = None) -> OptionInfo:  # type: ignore[override]
    if not names:
        names = ("",)
    return OptionInfo(default=default, names=tuple(names), help=help)


def _is_bool(annotation: Any) -> bool:
    if annotation is bool:
        return True
    origin = get_origin(annotation)
    if origin is Optional:
        return True
    if origin is not None:
        return any(_is_bool(arg) for arg in get_args(annotation))
    return False


def _is_path(annotation: Any) -> bool:
    if annotation is Path:
        return True
    origin = get_origin(annotation)
    if origin is not None:
        return any(_is_path(arg) for arg in get_args(annotation))
    return False


class Command:
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func)
        self.options: Dict[str, str] = {}
        self.defaults: Dict[str, Any] = {}
        for name, param in self.signature.parameters.items():
            default = param.default
            if isinstance(default, OptionInfo):
                canonical = name.replace("_", "-")
                option_names = tuple(opt or f"--{canonical}" for opt in default.names if opt)
                if not option_names:
                    option_names = (f"--{canonical}",)
                for option_name in option_names:
                    self.options[option_name] = name
                self.defaults[name] = default.default
            elif default is inspect._empty:
                self.defaults[name] = None
            else:
                self.defaults[name] = default

    def invoke(self, args: List[str]) -> Any:
        values = dict(self.defaults)
        consumed: Dict[str, Any] = {}
        i = 0
        while i < len(args):
            token = args[i]
            if token.startswith("--"):
                if token not in self.options:
                    raise BadParameter(f"Unknown option {token}")
                param_name = self.options[token]
                annotation = self.type_hints.get(
                    param_name, self.signature.parameters[param_name].annotation
                )
                if _is_bool(annotation) or isinstance(values.get(param_name), bool):
                    consumed[param_name] = True
                    i += 1
                    continue
                i += 1
                if i >= len(args):
                    raise BadParameter(f"Missing value for option {token}")
                value_token = args[i]
                if _is_path(annotation):
                    consumed[param_name] = Path(value_token)
                else:
                    consumed[param_name] = value_token
            else:
                raise BadParameter(f"Unexpected argument {token}")
            i += 1
        for name, param in self.signature.parameters.items():
            default = param.default
            if isinstance(default, OptionInfo) and default.default is ... and name not in consumed:
                raise BadParameter(f"Missing required option --{name.replace('_', '-')}")
        values.update(consumed)
        return self.func(**values)


class Typer:
    def __init__(self, help: str | None = None) -> None:
        self.help = help
        self.commands: Dict[str, Command] = {}

    def command(
        self, name: Optional[str] = None
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            command_name = name or func.__name__.replace("_", "-")
            self.commands[command_name] = Command(func)
            return func

        return decorator

    def invoke(self, args: List[str]) -> Any:
        if not args:
            raise BadParameter("No command provided")
        command_name, *command_args = args
        if command_name not in self.commands:
            raise BadParameter(f"Unknown command {command_name}")
        return self.commands[command_name].invoke(command_args)

    def __call__(self) -> None:  # pragma: no cover - parity with real Typer
        raise NotImplementedError("Direct invocation not supported in fallback")


class CliResult:
    def __init__(self, exit_code: int, stdout: str = "") -> None:
        self.exit_code = exit_code
        self.stdout = stdout


class CliRunner:
    def invoke(self, app: Typer, args: List[str]) -> CliResult:
        try:
            app.invoke(args)
        except Exit as exc:  # pragma: no cover - passthrough
            return CliResult(exit_code=exc.code)
        except Exception:
            return CliResult(exit_code=1)
        return CliResult(exit_code=0)


class testing:  # pragma: no cover - namespace shim
    CliRunner = CliRunner


__all__ = ["Typer", "Option", "Exit", "BadParameter", "CliRunner", "testing"]
