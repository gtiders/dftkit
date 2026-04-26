from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from ase import Atoms
from ase.build import make_supercell
from ase.geometry import find_mic
from ase.io import read
from ase.units import Bohr
import spglib

from dftkit.schemas.vasp.structure_analysis import CutoffRadiiInput

RTOL = 1e-5
ATOL = 1e-8


def _to_bohr(value: float) -> float:
    return round(value / Bohr, 8)


def _reduce_lattice(lattice: np.ndarray) -> np.ndarray:
    reduced = spglib.delaunay_reduce(np.array(lattice, dtype=float))
    if reduced is None:
        return np.array(lattice, dtype=float)
    return np.array(reduced, dtype=float)


def _shortest_lattice_vector(lattice: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    best_coefficients: np.ndarray | None = None
    best_vector: np.ndarray | None = None
    best_norm = np.inf
    sigma_min = float(np.min(np.linalg.svd(lattice, compute_uv=False)))
    radius = 1

    while True:
        for i in range(-radius, radius + 1):
            for j in range(-radius, radius + 1):
                for k in range(-radius, radius + 1):
                    coefficients = np.array([i, j, k], dtype=int)
                    if not np.any(coefficients):
                        continue
                    if max(abs(i), abs(j), abs(k)) != radius:
                        continue
                    vector = coefficients @ lattice
                    norm = float(np.linalg.norm(vector))
                    if norm < best_norm - 1e-12:
                        best_norm = norm
                        best_coefficients = coefficients
                        best_vector = vector

        if best_coefficients is None or best_vector is None:
            raise ValueError("Failed to locate a non-zero lattice vector")

        if best_norm <= sigma_min * (radius + 1):
            return best_coefficients, best_vector, best_norm
        radius += 1


def analyze_real_space_wigner_seitz(atoms: Atoms) -> dict[str, Any]:
    reduced_lattice = _reduce_lattice(np.array(atoms.cell.array, dtype=float))
    coefficients, shortest_vector, shortest_norm = _shortest_lattice_vector(reduced_lattice)
    inradius = shortest_norm / 2.0
    return {
        "inradius": round(inradius, 8),
        "inradius_bohr": _to_bohr(inradius),
        "shortest_lattice_vector_length": round(shortest_norm, 8),
        "shortest_lattice_vector_length_bohr": _to_bohr(shortest_norm),
        "shortest_lattice_vector_cartesian": [
            round(float(value), 8) for value in shortest_vector.tolist()
        ],
        "shortest_lattice_vector_coefficients": [int(value) for value in coefficients.tolist()],
        "reduced_lattice_matrix": [
            [round(float(value), 8) for value in row] for row in reduced_lattice.tolist()
        ],
    }


def _read_single_atoms(path: Path) -> Atoms:
    atoms = read(path, format="vasp")
    if isinstance(atoms, list):
        return atoms[-1]
    return atoms


def _parse_expansion_matrix(value: str) -> np.ndarray:
    text = value.replace("x", " ").replace("X", " ").replace(",", " ").replace(";", " ")
    try:
        numbers = [int(token) for token in text.split()]
    except ValueError as exc:
        raise ValueError("matrix must contain integers") from exc

    if len(numbers) == 3:
        return np.diag(numbers)
    if len(numbers) == 9:
        return np.asarray(numbers, dtype=int).reshape(3, 3)
    raise ValueError("matrix must contain either 3 or 9 integers")


def _build_or_read_supercell(primitive: Atoms, task_input: CutoffRadiiInput) -> tuple[Atoms, str]:
    if task_input.source_type == "matrix":
        if task_input.matrix is None:
            raise ValueError("matrix is required when source_type=matrix")
        matrix = _parse_expansion_matrix(task_input.matrix)
        supercell = make_supercell(primitive, matrix, wrap=True, order="atom-major")
        return supercell, np.array2string(matrix, separator=", ")

    supercell_path = task_input.supercell or Path("SPOSCAR")
    if not supercell_path.exists():
        raise ValueError(f"supercell file does not exist: {supercell_path}")
    return _read_single_atoms(supercell_path), str(supercell_path)


def _unique_sorted_distances(distances: np.ndarray) -> list[float]:
    unique: list[float] = []
    for distance in sorted(float(value) for value in distances):
        if not any(np.isclose(distance, existing, rtol=RTOL, atol=ATOL) for existing in unique):
            unique.append(distance)
    return unique


def _primitive_to_supercell_distances(primitive: Atoms, supercell: Atoms) -> np.ndarray:
    rows = []
    super_positions = supercell.get_positions()
    for position in primitive.get_positions():
        vectors = super_positions - position
        _, distances = find_mic(vectors, cell=supercell.cell, pbc=supercell.pbc)
        rows.append(distances)
    return np.asarray(rows)


def _calc_neighbor_cutoff(n: int, distances: np.ndarray) -> float:
    values: list[float] = []
    for row in distances:
        unique = _unique_sorted_distances(row)
        try:
            values.append(0.5 * (unique[n] + unique[n + 1]))
        except IndexError as exc:
            raise ValueError(
                "supercell is too small to determine all requested neighbour shells"
            ) from exc
    return max(values)


def _complete_neighbor_count(distances: np.ndarray) -> int:
    count = None
    for row in distances:
        unique = _unique_sorted_distances(row)
        atom_count = max(0, len(unique) - 2)
        count = atom_count if count is None else min(count, atom_count)
    return int(count or 0)


def run_cutoff_radii(task_input: CutoffRadiiInput) -> dict[str, Any]:
    primitive = _read_single_atoms(task_input.input)
    supercell, supercell_source = _build_or_read_supercell(primitive, task_input)

    max_cutoff_info = analyze_real_space_wigner_seitz(supercell)
    max_cutoff = float(max_cutoff_info["inradius"])

    distances = _primitive_to_supercell_distances(primitive, supercell)
    neighbor_count = _complete_neighbor_count(distances)
    radii: list[dict[str, Any]] = []
    for n in range(1, neighbor_count + 1):
        radius = _calc_neighbor_cutoff(n, distances)
        if radius > max_cutoff + ATOL:
            break
        radii.append(
            {
                "neighbor_shell": n,
                "cutoff_radius": round(radius, 8),
                "cutoff_radius_bohr": _to_bohr(radius),
            }
        )

    return {
        "task": "cutoff-radii",
        "primitive_input": str(task_input.input),
        "supercell_source": supercell_source,
        "natoms_primitive": len(primitive),
        "natoms_supercell": len(supercell),
        "maximum_cutoff_radius": round(max_cutoff, 8),
        "maximum_cutoff_radius_bohr": _to_bohr(max_cutoff),
        "maximum_cutoff_source": "real-space Wigner-Seitz inradius of the supercell",
        "neighbor_cutoff_radii": radii,
    }
