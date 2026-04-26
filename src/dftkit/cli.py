from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import click
from pydantic import ValidationError
from rich.console import Console

from dftkit.config import DEFAULT_PROVIDER, ensure_config_file, load_config
from dftkit.interactive import choose_task_interactively, prompt_task_params
from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.registry import PROVIDERS, get_provider, get_task_definition
from dftkit.ui import plain_table

console = Console()


def _option_type_name(prompt: PromptSpec) -> str:
    if prompt.choices:
        return "str"
    if prompt.parser is int:
        return "int"
    if prompt.parser is bool:
        return "bool"
    return "str"


def _format_task_option(prompt: PromptSpec) -> str:
    default = f", default={prompt.default}" if prompt.default is not None else ""
    return f"--{prompt.field_name.replace('_', '-')} <{_option_type_name(prompt)}>{default}"


def _task_help_text(provider: ProviderDefinition, task: TaskDefinition) -> str:
    lines = [
        f"{provider.display_name} Task {task.task_id}: {task.name}",
        "",
        task.description,
        "",
        "Options:",
    ]
    for prompt in task.prompts:
        lines.append(f"  {_format_task_option(prompt)}")
        lines.append(f"      {prompt.help}")
    return "\n".join(lines)


def _provider_help_text(provider: ProviderDefinition) -> str:
    return (
        f"{provider.display_name} provider\n\n"
        f"{provider.description}\n\n"
        f"Examples:\n"
        f"  dftkit {provider.provider_id} --list-tasks\n"
        f"  dftkit {provider.provider_id} --task 102 --help\n"
        f"  dftkit {provider.provider_id} --task 102 -- --input POSCAR\n"
    )


def _print_task_catalog(provider: ProviderDefinition) -> None:
    table = plain_table(f"{provider.display_name} Tasks")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Menu", style="magenta", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Summary")
    for task_id, task in sorted(provider.tasks.items()):
        table.add_row(task_id, task.group_id, task.name, task.summary)
    console.print(table)


def _parse_task_params(task_args: Sequence[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    i = 0
    while i < len(task_args):
        token = task_args[i]
        if not token.startswith("--"):
            raise click.ClickException(
                "Task parameters must be passed as --key value pairs after --."
            )
        key = token[2:].replace("-", "_")
        if not key:
            raise click.ClickException("Invalid empty task parameter name.")

        if i + 1 >= len(task_args) or task_args[i + 1].startswith("--"):
            params[key] = "true"
            i += 1
            continue

        params[key] = task_args[i + 1]
        i += 2
    return params


def _apply_task_defaults(task: TaskDefinition, params: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(params)
    for prompt in task.prompts:
        if prompt.field_name not in resolved and prompt.default is not None:
            resolved[prompt.field_name] = prompt.default
    return resolved


def _validate_task_input(task: TaskDefinition, params: dict[str, Any]) -> Any:
    try:
        return task.model.model_validate(params)
    except ValidationError as exc:
        raise click.ClickException(str(exc)) from exc


def _render_result(provider: ProviderDefinition, task: TaskDefinition, task_input: Any, result: dict[str, Any]) -> None:
    console.print(f"[bold]{provider.display_name}[/bold] Task {task.task_id} {task.name}")
    console.print(f"Menu {task.group_id}: {provider.group_names[task.group_id]}")
    console.print(task.summary)
    console.print("")

    input_table = plain_table("Validated Input")
    input_table.add_column("Field", style="cyan")
    input_table.add_column("Value", style="green")
    for field_name, value in task_input.model_dump(exclude_none=True).items():
        input_table.add_row(field_name, str(value))
    console.print(input_table)

    result_table = plain_table("Operation Result")
    result_table.add_column("Field", style="cyan")
    result_table.add_column("Value", style="green")
    for field_name, value in result.items():
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        elif isinstance(value, dict):
            rendered = ", ".join(f"{key}={item}" for key, item in value.items())
        else:
            rendered = str(value)
        result_table.add_row(field_name, rendered)
    console.print(result_table)


def _run_provider(provider: ProviderDefinition, task_id: str | None, list_tasks: bool, show_help: bool, raw_args: Sequence[str]) -> None:
    if list_tasks:
        _print_task_catalog(provider)
        return

    if show_help and not task_id:
        console.print(_provider_help_text(provider))
        return

    if not task_id:
        task = choose_task_interactively(provider)
        if task is None:
            console.print(f"Exiting {provider.display_name} mode.")
            return
        params = prompt_task_params(task)
        task_input = _validate_task_input(task, params)
        result = task.operation(task_input)
        _render_result(provider, task, task_input, result)
        return

    task = get_task_definition(provider, task_id)
    if not task:
        raise click.ClickException(
            f"Unknown task id for provider {provider.provider_id}: {task_id}"
        )

    if show_help:
        console.print(_task_help_text(provider, task))
        return

    params = _apply_task_defaults(task, _parse_task_params(raw_args))
    task_input = _validate_task_input(task, params)
    result = task.operation(task_input)
    _render_result(provider, task, task_input, result)


def _resolve_provider_or_fail(provider_id: str) -> ProviderDefinition:
    provider = get_provider(provider_id)
    if provider is None:
        supported = ", ".join(sorted(PROVIDERS))
        raise click.ClickException(
            f"Unknown provider: {provider_id}. Supported providers: {supported}"
        )
    return provider


def _provider_command(provider_id: str):
    @click.command(
        name=provider_id,
        context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
    )
    @click.option("--task", "task_id", help="Numeric task id, for example 102.")
    @click.option("--list-tasks", is_flag=True, help="List all registered tasks.")
    @click.option("--help", "show_help", is_flag=True, help="Show provider or task help.")
    @click.pass_context
    def command(
        ctx: click.Context, task_id: str | None, list_tasks: bool, show_help: bool
    ) -> None:
        provider = _resolve_provider_or_fail(provider_id)
        _run_provider(provider, task_id, list_tasks, show_help, list(ctx.args))

    return command


@click.group(invoke_without_command=True, add_help_option=False)
@click.option("--task", "task_id", help="Numeric task id for the default provider.")
@click.option("--list-tasks", is_flag=True, help="List tasks for the default provider.")
@click.option("--help", "show_help", is_flag=True, help="Show root, provider, or task help.")
@click.pass_context
def main(
    ctx: click.Context, task_id: str | None, list_tasks: bool, show_help: bool
) -> None:
    """Provider-aware task-driven CLI entrypoint for DFT workflows."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    provider_id = config.default_provider or DEFAULT_PROVIDER
    provider = get_provider(provider_id) or get_provider(DEFAULT_PROVIDER)
    if provider is None:
        raise click.ClickException("No valid providers are registered.")
    _run_provider(provider, task_id, list_tasks, show_help, list(ctx.args))


@main.command("providers")
def list_providers() -> None:
    """List available providers and the active default."""
    config = load_config()
    ensure_config_file()
    effective_default = (
        config.default_provider if config.default_provider in PROVIDERS else DEFAULT_PROVIDER
    )
    table = plain_table("Available Providers")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Default", style="magenta", no_wrap=True)
    table.add_column("Description")
    for provider_id, provider in sorted(PROVIDERS.items()):
        default_marker = "*" if provider_id == effective_default else ""
        table.add_row(provider_id, default_marker, provider.description)
    console.print(table)
    console.print(f"Config file: {ensure_config_file()}")


main.add_command(_provider_command("vasp"))
main.add_command(_provider_command("abacus"))
