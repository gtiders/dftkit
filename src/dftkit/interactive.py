from __future__ import annotations

from itertools import zip_longest

import click
from rich.console import Console

from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.registry import get_group_definitions, get_task_definition
from dftkit.ui import plain_table

console = Console()


def _format_prompt_label(prompt: PromptSpec) -> str:
    return f"{prompt.prompt}: {prompt.help}"


def _input_with_marker(marker: str | None = None) -> str:
    rendered = marker or "[bold]>[/bold]"
    return console.input(f"{rendered} ").strip()


def _prompt_for_value(prompt: PromptSpec) -> object:
    label = _format_prompt_label(prompt)
    marker = prompt.input_marker
    if prompt.preface:
        console.print(prompt.preface)
    if prompt.choices:
        console.print(prompt.prompt)
        for key, text in prompt.choices:
            console.print(f"  {key}  {text}")
        while True:
            raw = _input_with_marker(marker)
            if not raw and prompt.default is not None:
                return prompt.default
            if any(raw == key for key, _ in prompt.choices):
                return raw
            console.print("[red]Please choose one of the listed options.[/red]")
    if prompt.parser in {int, float}:
        while True:
            suffix = f" [{prompt.default}]" if prompt.default is not None else ""
            console.print(f"{label}{suffix}")
            raw = _input_with_marker(marker)
            if not raw and prompt.default is not None:
                return prompt.default
            try:
                return prompt.parser(raw)
            except ValueError:
                if prompt.parser is int:
                    console.print("[red]Please enter an integer value.[/red]")
                else:
                    console.print("[red]Please enter a numeric value.[/red]")
    if prompt.parser is not None:
        default = prompt.default if isinstance(prompt.default, bool) else False
        default_hint = "Y/n" if default else "y/N"
        while True:
            console.print(f"{label} [{default_hint}]")
            raw = _input_with_marker(marker)
            if not raw:
                return default
            normalized = raw.lower()
            if normalized in {"y", "yes"}:
                return True
            if normalized in {"n", "no"}:
                return False
            console.print("[red]Please answer y or n.[/red]")
    suffix = f" [{prompt.default}]" if prompt.default is not None else ""
    console.print(f"{label}{suffix}")
    raw = _input_with_marker(marker)
    if not raw and prompt.default is not None:
        return prompt.default
    return raw


def _prompt_is_visible(prompt: PromptSpec, values: dict[str, object]) -> bool:
    if prompt.visible_if_field is None:
        return True
    if prompt.visible_if_field not in values:
        return False
    return values[prompt.visible_if_field] in prompt.visible_if_values


def prompt_task_params(task: TaskDefinition) -> dict[str, object]:
    console.print(f"[bold]Task {task.task_id}[/bold] {task.name}")
    console.print(task.description)
    if not task.prompts:
        return {}
    console.print("Enter values for the following options.")
    values: dict[str, object] = {}
    for prompt in task.prompts:
        if not _prompt_is_visible(prompt, values):
            continue
        raw_value = _prompt_for_value(prompt)
        if prompt.parser is not None and prompt.parser not in {int, float}:
            raw_value = prompt.parser(str(raw_value))
        values[prompt.field_name] = raw_value
    return values


def _pairwise_rows(items: list[str]) -> list[tuple[str, str]]:
    left_items = items[::2]
    right_items = items[1::2]
    return list(zip_longest(left_items, right_items, fillvalue=""))


def _render_top_menu(provider: ProviderDefinition) -> None:
    console.print(f"[bold]{provider.display_name} Main Menu[/bold]")
    table = plain_table("", show_header=False)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="cyan", no_wrap=True)
    items = [
        f"{group_id}  {group_name}"
        for group_id, group_name in sorted(provider.group_names.items())
    ]
    for left, right in _pairwise_rows(items):
        table.add_row(left, right)
    console.print(table)
    console.print("Input 0-9 to enter a menu, or q to quit.")


def _render_group_menu(provider: ProviderDefinition, group_id: str) -> None:
    console.print(
        f"[bold]{provider.display_name} Menu {group_id}[/bold]  {provider.group_names[group_id]}"
    )
    table = plain_table("", show_header=False)
    table.add_column(style="green", no_wrap=True)
    table.add_column(style="green", no_wrap=True)
    items = [
        f"{task.task_id}  {task.name}"
        for task in get_group_definitions(provider, group_id)
    ]
    for left, right in _pairwise_rows(items):
        table.add_row(left, right)
    console.print(table)
    console.print("Input a task id to enter that workflow, or q to go back.")


def choose_task_interactively(provider: ProviderDefinition) -> TaskDefinition | None:
    while True:
        _render_top_menu(provider)
        choice = _input_with_marker().lower()
        if choice == "q":
            return None
        direct_task = get_task_definition(provider, choice)
        if direct_task is not None:
            return direct_task
        if choice not in provider.group_names:
            console.print(f"[red]Unknown menu: {choice}[/red]")
            continue

        while True:
            _render_group_menu(provider, choice)
            task_choice = _input_with_marker().lower()
            if task_choice == "q":
                break

            task = get_task_definition(provider, task_choice)
            if task is None or task.group_id != choice:
                console.print(
                    f"[red]Unknown task id in menu {choice}: {task_choice}[/red]"
                )
                continue
            return task
