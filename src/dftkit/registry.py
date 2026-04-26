from __future__ import annotations

from dftkit.models import ProviderDefinition, TaskDefinition
from dftkit.providers.abacus import PROVIDER as ABACUS_PROVIDER
from dftkit.providers.vasp import PROVIDER as VASP_PROVIDER

PROVIDERS: dict[str, ProviderDefinition] = {
    "vasp": VASP_PROVIDER,
    "abacus": ABACUS_PROVIDER,
}


def get_provider(provider_id: str) -> ProviderDefinition | None:
    return PROVIDERS.get(provider_id)


def get_task_definition(provider: ProviderDefinition, task_id: str) -> TaskDefinition | None:
    return provider.tasks.get(task_id)


def get_group_definitions(provider: ProviderDefinition, group_id: str) -> list[TaskDefinition]:
    return sorted(
        (item for item in provider.tasks.values() if item.group_id == group_id),
        key=lambda item: item.task_id,
    )
