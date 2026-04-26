from __future__ import annotations

from typing import Any

import numpy as np
from ase.build import make_supercell
from ase.io import read
from ase.io.vasp import write_vasp

from dftkit.schemas.vasp.structure_analysis import SupercellBuildInput


def _write_poscar(path, atoms) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, atoms, direct=True, sort=True)


def _format_matrix(matrix: np.ndarray) -> str:
    rows = ["[" + ", ".join(f"{value: .8f}" for value in row) + "]" for row in matrix]
    return "\n".join(rows)


def run_supercell_build(task_input: SupercellBuildInput) -> dict[str, Any]:
    source_atoms = read(task_input.input, format="vasp")
    matrix = np.array(task_input.matrix, dtype=int)
    supercell_atoms = make_supercell(
        source_atoms,
        matrix,
        wrap=True,
        order="atom-major",
    )
    _write_poscar(task_input.output, supercell_atoms)
    return {
        "task": "supercell-build",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "natoms_in": len(source_atoms),
        "natoms_out": len(supercell_atoms),
        "supercell_matrix": _format_matrix(matrix.astype(float)),
        "atom_order": "atom-major",
    }
