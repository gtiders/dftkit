from __future__ import annotations

from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.operations.gpumd.kpath import run_kpath_generate
from dftkit.operations.gpumd.structure import run_structure_info
from dftkit.schemas.gpumd.kpath import KPathGenerateInput
from dftkit.schemas.gpumd.structure import StructureInfoInput

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
        summary="Inspect a structure file for GPUMD.",
        description=(
            "Read a structure file in the GPUMD context and report basic lattice, "
            "atom count, chemical formula, and symmetry metadata."
        ),
        model=StructureInfoInput,
        operation=run_structure_info,
        prompts=(
            PromptSpec("input", "Input structure file", "xyz.in, CIF, XYZ, or another ASE-readable file."),
            PromptSpec("format", "Input format", "Leave empty for ASE auto detection.", default="auto"),
            PromptSpec(
                "symmetry",
                "Run symmetry analysis?",
                "Use spglib to infer space group information.",
                parser=_bool_parser,
                default=True,
            ),
        ),
    ),
    "902": TaskDefinition(
        task_id="902",
        name="kpath-generate",
        group_id="9",
        summary="Generate a high-symmetry k-path for GPUMD.",
        description="Standardize the structure and build a high-symmetry k-path for the GPUMD context.",
        model=KPathGenerateInput,
        operation=run_kpath_generate,
        prompts=(
            PromptSpec("input", "Input structure file", "xyz.in or CIF recommended."),
            PromptSpec("code", "Target code", "Output style such as gpumd.", default="gpumd"),
            PromptSpec("line_density", "Line density", "Number of points per reciprocal length unit.", parser=int, default=20),
            PromptSpec("primitive", "Reduce to primitive cell?", "Recommended for standard k-path generation.", parser=_bool_parser, default=True),
            PromptSpec("output", "Output file", "File path for the generated k-path text.", default="KPOINTS"),
        ),
    ),
}

PROVIDER = ProviderDefinition(
    provider_id="gpumd",
    display_name="GPUMD",
    description="GPUMD oriented task menu.",
    group_names=GROUP_NAMES,
    tasks=TASKS,
)
