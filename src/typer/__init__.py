"""Minimal Typer-compatible shim for testing without external dependency."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, get_args, get_origin, get_type_hints


class Exit(Exception):
    def __init__(self, code: int = 0) -> None:
        super().__init__(code)
        self.code = code


@dataclass
class OptionInfo:
    default: Any
    names: List[str]
    help: Optional[str] = None


def Option(default: Any, *names: str, help: str | None = None) -> OptionInfo:  # type: ignore[override]
    names_list = [name for name in names if name.startswith("--")]
    return OptionInfo(default=default, names=names_list, help=help)


def _is_bool(annotation: Any) -> bool:
    if annotation is bool:
        return True
    origin = get_origin(annotation)
    if origin is Optional:
        return True
    if origin is list or origin is dict:
        return False
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
                for option_name in default.names:
                    self.options[option_name] = name
                self.defaults[name] = default.default
            elif default is inspect._empty:
                self.defaults[name] = None
            else:
                self.defaults[name] = default

    def invoke(self, args: List[str]) -> Any:
        values = dict(self.defaults)
        used: Dict[str, Any] = {}
        i = 0
        while i < len(args):
            token = args[i]
            if token.startswith("--"):
                if token not in self.options:
                    raise ValueError(f"Unknown option {token}")
                param_name = self.options[token]
                annotation = self.type_hints.get(param_name, self.signature.parameters[param_name].annotation)
                if _is_bool(annotation) or isinstance(values.get(param_name), bool):
                    used[param_name] = True
                    i += 1
                    continue
                i += 1
                if i >= len(args):
                    raise ValueError(f"Missing value for option {token}")
                value_token = args[i]
                if _is_path(annotation):
                    used[param_name] = Path(value_token)
                else:
                    used[param_name] = value_token
            else:
                pass
            i += 1
        for name, param in self.signature.parameters.items():
            default = param.default
            if isinstance(default, OptionInfo) and default.default is ... and name not in used:
                raise ValueError(f"Missing required option for parameter {name}")
        values.update(used)
        return self.func(**values)


class Typer:
    def __init__(self, help: str | None = None) -> None:
        self.help = help
        self.commands: Dict[str, Command] = {}
        self.default_command: Optional[Command] = None

    def command(self, name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            command_name = name or func.__name__.replace("_", "-")
            cmd = Command(func)
            if command_name in ("main", "__call__"):
                self.default_command = cmd
            self.commands[command_name] = cmd
            return func

        return decorator

    def invoke(self, args: List[str]) -> Any:
        if not args:
            if self.default_command:
                return self.default_command.invoke([])
            raise ValueError("No command provided")
        command_name, *command_args = args
        if command_name not in self.commands:
            raise ValueError(f"Unknown command {command_name}")
        return self.commands[command_name].invoke(command_args)

    def __call__(self) -> None:
        raise NotImplementedError("Direct invocation not supported in shim")


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


__all__ = [
    "Typer",
    "Option",
    "Exit",
    "CliRunner",
    "testing",
]
