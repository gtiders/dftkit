from __future__ import annotations

from dftkit.models import ProviderDefinition, TaskDefinition
from dftkit.providers.alamode import PROVIDER as ALAMODE_PROVIDER
from dftkit.providers.abacus import PROVIDER as ABACUS_PROVIDER
from dftkit.providers.gpumd import PROVIDER as GPUMD_PROVIDER
from dftkit.providers.shengbte import PROVIDER as SHENGBTE_PROVIDER
from dftkit.providers.vasp import PROVIDER as VASP_PROVIDER

PROVIDERS: dict[str, ProviderDefinition] = {
    "alamode": ALAMODE_PROVIDER,
    "gpumd": GPUMD_PROVIDER,
    "shengbte": SHENGBTE_PROVIDER,
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
