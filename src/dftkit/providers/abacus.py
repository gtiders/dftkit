from __future__ import annotations

from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.operations.abacus.kpath import run_kpath_generate
from dftkit.operations.abacus.structure import run_structure_info
from dftkit.schemas.abacus.kpath import KPathGenerateInput
from dftkit.schemas.abacus.structure import StructureInfoInput

GROUP_NAMES: dict[str, str] = {
    "0": "General Utilities",
    "1": "Structure Analysis",
    "2": "File Conversion",
    "3": "Electronic Structure",
    "4": "Density of States",
    "5": "Charge and Wavefunction",
    "6": "Phonon and Vibrations",
    "7": "Molecular Dynamics",
    "8": "Post-processing",
    "9": "K-Path and Brillouin Zone",
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
    "902": TaskDefinition(
        task_id="902",
        name="kpath-generate",
        group_id="9",
        summary="Generate a high-symmetry k-path for ABACUS.",
        description=(
            "Standardize the structure and build a high-symmetry k-path for the "
            "ABACUS context."
        ),
        model=KPathGenerateInput,
        operation=run_kpath_generate,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input structure file",
                help="STRU or CIF recommended.",
            ),
            PromptSpec(
                field_name="code",
                prompt="Target code",
                help="Output style such as abacus.",
                default="abacus",
            ),
            PromptSpec(
                field_name="line_density",
                prompt="Line density",
                help="Number of points per reciprocal length unit.",
                parser=int,
                default=20,
            ),
            PromptSpec(
                field_name="primitive",
                prompt="Reduce to primitive cell?",
                help="Recommended for standard k-path generation.",
                parser=_bool_parser,
                default=True,
            ),
            PromptSpec(
                field_name="output",
                prompt="Output file",
                help="File path for the generated k-path text.",
                default="KPOINTS",
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
