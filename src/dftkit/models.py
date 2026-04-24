from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class PromptSpec:
    field_name: str
    prompt: str
    help: str
    parser: Any | None = None
    default: Any | None = None
    preface: str | None = None
    input_marker: str | None = None
    choices: tuple[tuple[str, str], ...] = ()
    visible_if_field: str | None = None
    visible_if_values: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    task_id: str
    name: str
    group_id: str
    summary: str
    description: str
    model: type[BaseModel]
    operation: Any
    prompts: tuple[PromptSpec, ...]


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    provider_id: str
    display_name: str
    description: str
    group_names: dict[str, str]
    tasks: dict[str, TaskDefinition]
