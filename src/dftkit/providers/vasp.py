from __future__ import annotations

from dftkit.models import PromptSpec, ProviderDefinition, TaskDefinition
from dftkit.operations.vasp.task_001_kpoints_mesh import run_kpoints_mesh
from dftkit.operations.vasp.task_002_band_kpoints_prepare import (
    run_band_kpoints_prepare,
)
from dftkit.operations.vasp.task_102_structure_info import run_structure_info
from dftkit.operations.vasp.task_103_primitive_standardize import (
    run_primitive_standardize,
)
from dftkit.operations.vasp.task_104_conventional_standardize import (
    run_conventional_standardize,
)
from dftkit.operations.vasp.task_105_supercell_build import run_supercell_build
from dftkit.operations.vasp.task_106_cutoff_radii import run_cutoff_radii
from dftkit.operations.vasp.task_108_stacking_grid import run_stacking_grid
from dftkit.operations.vasp.task_201_stru_to_poscar_convert import (
    run_stru_to_poscar_convert,
)
from dftkit.schemas.vasp.file_conversion import StruToPoscarInput
from dftkit.schemas.vasp.input_files import BandPathInput, KpointsMeshInput
from dftkit.schemas.vasp.structure_analysis import (
    ConventionalStandardizeInput,
    CutoffRadiiInput,
    PrimitiveStandardizeInput,
    StackingGridInput,
    StructureInfoInput,
    SupercellBuildInput,
)

GROUP_NAMES: dict[str, str] = {
    "0": "VASP Input-Files Generator",
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


def _cutoff_source_parser(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"1", "file"}:
        return "file"
    if normalized in {"2", "matrix"}:
        return "matrix"
    raise ValueError(f"Invalid cutoff source: {value}")


TASKS: dict[str, TaskDefinition] = {
    "002": TaskDefinition(
        task_id="002",
        name="band-kpoints-prepare",
        group_id="0",
        summary="Generate line-mode KPOINTS and kpath.yaml from POSCAR.",
        description=(
            "Read POSCAR from the current directory, use seekpath to generate a "
            "high-symmetry band path, write line-mode KPOINTS, and write kpath.yaml."
        ),
        model=BandPathInput,
        operation=run_band_kpoints_prepare,
        prompts=(
            PromptSpec(
                field_name="line_density",
                prompt="Input line density",
                help="Number of points for each path segment in line-mode KPOINTS.",
                parser=int,
                default=20,
            ),
        ),
    ),
    "001": TaskDefinition(
        task_id="001",
        name="kpoints-mesh-generate",
        group_id="0",
        summary="Generate a regular KPOINTS mesh from POSCAR.",
        description=(
            "Read POSCAR from the current directory, generate a regular KPOINTS "
            "mesh in Gamma or Monkhorst-Pack mode from the requested reciprocal "
            "space resolution, and write KPOINTS."
        ),
        model=KpointsMeshInput,
        operation=run_kpoints_mesh,
        prompts=(
            PromptSpec(
                field_name="mode",
                prompt="Select mesh mode",
                help="Choose the regular mesh mode.",
                choices=(("1", "Gamma"), ("2", "Monkhorst-Pack")),
            ),
            PromptSpec(
                field_name="kpr",
                prompt="Input KPT-Resolved Value",
                help="e.g., 0.04, in unit of 2*PI/Angstrom.",
                parser=float,
                default=0.04,
                preface=(
                    "+-------------------------- Warm Tips --------------------------+\n"
                    "\n"
                    " * Accuracy Levels: Gamma-Only: 0;\n"
                    "   Low: 0.06~0.04;\n"
                    "   Medium: 0.04~0.03;\n"
                    "   Fine: 0.02~0.01.\n"
                    " * 0.03-0.04 is Generally Precise Enough!\n"
                    "+---------------------------------------------------------------+"
                ),
                input_marker="[bold]------------>>[/bold]",
            ),
        ),
    ),
    "102": TaskDefinition(
        task_id="102",
        name="structure-info",
        group_id="1",
        summary="Inspect a structure file for VASP.",
        description=(
            "Read POSCAR from the current directory, perform ordinary structure "
            "analysis together with symmetry analysis, print the summary in the "
            "terminal, and write the full result to symmetry.yaml."
        ),
        model=StructureInfoInput,
        operation=run_structure_info,
        prompts=(),
    ),
    "103": TaskDefinition(
        task_id="103",
        name="primitive-standardize",
        group_id="1",
        summary="Convert POSCAR to the standard primitive cell.",
        description=(
            "Read POSCAR from the current directory, convert it to the standard "
            "primitive cell with spglib, write PPOSCAR in direct coordinates, "
            "and print the lattice transformation matrices."
        ),
        model=PrimitiveStandardizeInput,
        operation=run_primitive_standardize,
        prompts=(),
    ),
    "104": TaskDefinition(
        task_id="104",
        name="conventional-standardize",
        group_id="1",
        summary="Convert POSCAR to the standard conventional cell.",
        description=(
            "Read POSCAR from the current directory, convert it to the standard "
            "conventional cell with spglib, write CPOSCAR in direct coordinates, "
            "and print the lattice transformation matrices."
        ),
        model=ConventionalStandardizeInput,
        operation=run_conventional_standardize,
        prompts=(),
    ),
    "105": TaskDefinition(
        task_id="105",
        name="supercell-build",
        group_id="1",
        summary="Build a supercell from POSCAR and write SPOSCAR.",
        description=(
            "Read POSCAR from the current directory, build a supercell with ASE "
            "using atom-major ordering, write SPOSCAR in direct coordinates, "
            "and print the supercell matrix."
        ),
        model=SupercellBuildInput,
        operation=run_supercell_build,
        prompts=(
            PromptSpec(
                field_name="matrix",
                prompt="Supercell matrix",
                help="Enter 3 integers for a diagonal matrix or 9 integers for a full 3x3 matrix.",
            ),
        ),
    ),
    "106": TaskDefinition(
        task_id="106",
        name="cutoff-radii",
        group_id="1",
        summary="Estimate maximum cutoff and neighbor shell radii from POSCAR and SPOSCAR.",
        description=(
            "Read primitive POSCAR together with SPOSCAR or an expansion matrix, "
            "use the supercell real-space Wigner-Seitz inradius as the maximum cutoff, "
            "then print neighbor shell cutoff radii that fit inside that maximum cutoff."
        ),
        model=CutoffRadiiInput,
        operation=run_cutoff_radii,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Primitive structure file",
                help="Usually POSCAR.",
                default="POSCAR",
            ),
            PromptSpec(
                field_name="source_type",
                prompt="Select supercell source",
                help="Choose whether to read a supercell file or build it from an expansion matrix.",
                parser=_cutoff_source_parser,
                choices=(("1", "Supercell file"), ("2", "Expansion matrix")),
                default="1",
            ),
            PromptSpec(
                field_name="supercell",
                prompt="Supercell file",
                help="Usually SPOSCAR.",
                default="SPOSCAR",
                visible_if_field="source_type",
                visible_if_values=("file",),
            ),
            PromptSpec(
                field_name="matrix",
                prompt="Expansion matrix",
                help="Example: 2x2x3 or 2 0 0 0 2 0 0 0 3.",
                visible_if_field="source_type",
                visible_if_values=("matrix",),
            ),
        ),
    ),
    "108": TaskDefinition(
        task_id="108",
        name="stacking-grid-generate",
        group_id="1",
        summary="Generate bilayer stacking-grid POSCARs by translating one layer.",
        description=(
            "Read a bilayer POSCAR, treat the single zero-grid axis as the vacuum "
            "direction, split the two layers by fractional cut, and write a grid "
            "of translated structures in subdirectories under the output folder."
        ),
        model=StackingGridInput,
        operation=run_stacking_grid,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input bilayer POSCAR",
                help="Usually monolayer POSCAR.",
                default="POSCAR",
            ),
            PromptSpec(
                field_name="a_grid",
                prompt="Grid points along a",
                help="Use 0 if a is the vacuum axis.",
                default=0,
            ),
            PromptSpec(
                field_name="b_grid",
                prompt="Grid points along b",
                help="Use 0 if b is the vacuum axis.",
                default=0,
            ),
            PromptSpec(
                field_name="c_grid",
                prompt="Grid points along c",
                help="Use 0 if c is the vacuum axis.",
                default=0,
            ),
            PromptSpec(
                field_name="output",
                prompt="Output directory",
                help="Root directory for the generated stacking subfolders.",
                default="stacking_grid",
            ),
            PromptSpec(
                field_name="cut",
                prompt="Layer split cut",
                help="Fractional cut on the vacuum axis used to split upper and lower layers.",
                parser=float,
                default=0.5,
            ),
            PromptSpec(
                field_name="move",
                prompt="Moving layer",
                help="Choose which layer to translate.",
                choices=(("upper", "Upper"), ("lower", "Lower")),
                default="upper",
            ),
            PromptSpec(
                field_name="tol",
                prompt="Cut tolerance",
                help="Atoms closer than this to the cut will trigger an error.",
                parser=float,
                default=1e-6,
            ),
            PromptSpec(
                field_name="skip_origin",
                prompt="Skip origin structure",
                help="If true, do not write the unshifted structure.",
                parser=_bool_parser,
                default=False,
            ),
            PromptSpec(
                field_name="overwrite",
                prompt="Overwrite existing files",
                help="If true, replace existing POSCAR files in output directories.",
                parser=_bool_parser,
                default=False,
            ),
        ),
    ),
    "201": TaskDefinition(
        task_id="201",
        name="stru-to-poscar-convert",
        group_id="2",
        summary="Convert ABACUS STRU to POSCAR with optional a/c swap.",
        description=(
            "Read an ABACUS STRU file through dpdata, optionally swap the a and c "
            "axes to reverse the paired ABACUS conversion convention, and write a "
            "VASP POSCAR file."
        ),
        model=StruToPoscarInput,
        operation=run_stru_to_poscar_convert,
        prompts=(
            PromptSpec(
                field_name="input",
                prompt="Input STRU",
                help="Usually STRU.",
                default="STRU",
            ),
            PromptSpec(
                field_name="output",
                prompt="Output POSCAR",
                help="Usually POSCAR.",
                default="POSCAR",
            ),
        ),
    ),
}


PROVIDER = ProviderDefinition(
    provider_id="vasp",
    display_name="VASP",
    description="Default VASP-oriented task menu.",
    group_names=GROUP_NAMES,
    tasks=TASKS,
)
