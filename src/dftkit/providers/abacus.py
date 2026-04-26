from __future__ import annotations

from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.operations.abacus.task_201_poscar_to_stru_convert import (
    run_poscar_to_stru_convert,
)
from dftkit.operations.abacus.task_202_poscar_to_stru_swap_ac_convert import (
    run_poscar_to_stru_swap_ac_convert,
)
from dftkit.operations.abacus.task_102_structure_info import run_structure_info
from dftkit.schemas.abacus.file_conversion import (
    PoscarToStruInput,
    PoscarToStruSwapACInput,
)
from dftkit.schemas.abacus.structure_analysis import StructureInfoInput

GROUP_NAMES: dict[str, str] = {
    "1": "Structure Analysis",
    "2": "File Conversion",
}


def _bool_parser(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


TASKS: dict[str, TaskDefinition] = {
    "102": TaskDefinition(
        task_id="102",
        name="structure-info",
        group_id="1",
        summary="Inspect a structure file for ABACUS.",
        description=(
            "Read a structure file in the ABACUS context and report basic lattice, "
            "atom count, chemical formula, and symmetry metadata."
        ),
        model=StructureInfoInput,
        operation=run_structure_info,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input structure file",
                help="STRU, CIF, XYZ, or another ASE-readable file.",
            ),
            PromptSpec(
                field_name="format",
                prompt="Input format",
                help="Leave empty for ASE auto detection.",
                default="auto",
            ),
            PromptSpec(
                field_name="symmetry",
                prompt="Run symmetry analysis?",
                help="Use spglib to infer space group information.",
                parser=_bool_parser,
                default=True,
            ),
        ),
    ),
    "201": TaskDefinition(
        task_id="201",
        name="poscar-to-stru-convert",
        group_id="2",
        summary="Convert POSCAR to ABACUS STRU.",
        description=(
            "Read a POSCAR file and write an ABACUS STRU file through dpdata. "
            "Optional pseudopotential and orbital mappings may be supplied through "
            "a JSON file."
        ),
        model=PoscarToStruInput,
        operation=run_poscar_to_stru_convert,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input POSCAR",
                help="Usually POSCAR.",
                default="POSCAR",
            ),
            PromptSpec(
                field_name="output",
                prompt="Output STRU",
                help="Usually STRU.",
                default="STRU",
            ),
            PromptSpec(
                field_name="basis_json",
                prompt="Basis JSON",
                help="Optional JSON file with pp_file and numerical_orbital mappings.",
            ),
        ),
    ),
    "202": TaskDefinition(
        task_id="202",
        name="poscar-to-stru-swap-ac-convert",
        group_id="2",
        summary="Convert POSCAR to ABACUS STRU after swapping a and c axes.",
        description=(
            "Read a POSCAR file, swap the a and c axes while preserving the "
            "handedness convention of the original conversion script, then write "
            "an ABACUS STRU file through dpdata. Optional pseudopotential and "
            "orbital mappings may be supplied through a JSON file."
        ),
        model=PoscarToStruSwapACInput,
        operation=run_poscar_to_stru_swap_ac_convert,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input POSCAR",
                help="Usually POSCAR.",
                default="POSCAR",
            ),
            PromptSpec(
                field_name="output",
                prompt="Output STRU",
                help="Usually STRU.",
                default="STRU",
            ),
            PromptSpec(
                field_name="basis_json",
                prompt="Basis JSON",
                help="Optional JSON file with pp_file and numerical_orbital mappings.",
            ),
        ),
    ),
}


PROVIDER = ProviderDefinition(
    provider_id="abacus",
    display_name="ABACUS",
    description="ABACUS oriented task menu.",
    group_names=GROUP_NAMES,
    tasks=TASKS,
)
