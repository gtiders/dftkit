from __future__ import annotations

from typing import Any

import numpy as np
from ase import Atoms
from ase.io import read
from ase.io.vasp import write_vasp
import spglib

from dftkit.schemas.vasp.structure_analysis import ConventionalStandardizeInput


def _atoms_to_spglib_cell(atoms: Atoms) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.array(atoms.cell.array, dtype=float),
        np.array(atoms.get_scaled_positions(), dtype=float),
        np.array(atoms.get_atomic_numbers(), dtype=int),
    )


def _spglib_cell_to_atoms(cell: tuple[np.ndarray, np.ndarray, np.ndarray]) -> Atoms:
    lattice, positions, numbers = cell
    return Atoms(
        numbers=list(numbers),
        cell=np.array(lattice, dtype=float),
        scaled_positions=np.array(positions, dtype=float),
        pbc=True,
    )


def _write_poscar(path, atoms: Atoms) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, atoms, direct=True, sort=True)


def _format_matrix(matrix: np.ndarray) -> str:
    rows = ["[" + ", ".join(f"{value: .8f}" for value in row) + "]" for row in matrix]
    return "\n".join(rows)


def run_conventional_standardize(
    task_input: ConventionalStandardizeInput,
) -> dict[str, Any]:
    source_atoms = read(task_input.input, format="vasp")
    source_lattice = np.array(source_atoms.cell.array, dtype=float)
    standardized_cell = spglib.standardize_cell(
        _atoms_to_spglib_cell(source_atoms),
        to_primitive=False,
        no_idealize=False,
        symprec=task_input.symprec,
        angle_tolerance=task_input.angle_tolerance,
    )
    if standardized_cell is None:
        raise ValueError("spglib failed to standardize the input structure")

    target_atoms = _spglib_cell_to_atoms(standardized_cell)
    target_lattice = np.array(target_atoms.cell.array, dtype=float)
    transform = target_lattice @ np.linalg.inv(source_lattice)
    inverse_transform = np.linalg.inv(transform)
    _write_poscar(task_input.output, target_atoms)

    return {
        "task": "conventional-standardize",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "natoms_in": len(source_atoms),
        "natoms_out": len(target_atoms),
        "lattice_transform": _format_matrix(transform),
        "inverse_lattice_transform": _format_matrix(inverse_transform),
    }
