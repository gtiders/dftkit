from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from ase.io import read
from ruamel.yaml import YAML
import spglib

from dftkit.schemas.vasp.structure_analysis import StructureInfoInput

yaml = YAML()
yaml.default_flow_style = False


def _crystal_system(spacegroup_number: int) -> str:
    if 1 <= spacegroup_number <= 2:
        return "triclinic"
    if 3 <= spacegroup_number <= 15:
        return "monoclinic"
    if 16 <= spacegroup_number <= 74:
        return "orthorhombic"
    if 75 <= spacegroup_number <= 142:
        return "tetragonal"
    if 143 <= spacegroup_number <= 167:
        return "trigonal"
    if 168 <= spacegroup_number <= 194:
        return "hexagonal"
    return "cubic"


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.dump(data, handle)


def run_structure_info(task_input: StructureInfoInput) -> dict[str, Any]:
    atoms = read(
        task_input.input,
        format=None if task_input.format == "auto" else task_input.format,
    )
    analysis: dict[str, Any] = {
        "task": "structure-info",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "formula": atoms.get_chemical_formula(),
        "natoms": len(atoms),
        "volume": round(float(atoms.get_volume()), 8),
        "cell_lengths": [round(float(value), 8) for value in atoms.cell.lengths()],
        "cell_angles": [round(float(value), 8) for value in atoms.cell.angles()],
        "lattice_matrix": [
            [round(float(value), 8) for value in row] for row in atoms.cell.array.tolist()
        ],
        "pbc": [bool(value) for value in atoms.pbc],
        "elements": sorted(set(atoms.get_chemical_symbols())),
        "counts": {
            str(symbol): int(count)
            for symbol, count in zip(*np.unique(atoms.get_chemical_symbols(), return_counts=True))
        },
        "positions_fractional": [
            [round(float(value), 8) for value in row]
            for row in atoms.get_scaled_positions().tolist()
        ],
    }
    if task_input.symmetry:
        cell = (
            atoms.cell.array,
            atoms.get_scaled_positions(),
            atoms.get_atomic_numbers(),
        )
        symmetry_dataset = spglib.get_symmetry_dataset(cell)
        if symmetry_dataset is not None:
            analysis["symmetry"] = {
                "spacegroup_number": int(symmetry_dataset.number),
                "international_symbol": str(symmetry_dataset.international),
                "hall_symbol": str(symmetry_dataset.hall),
                "point_group": str(symmetry_dataset.pointgroup),
                "crystal_system": _crystal_system(int(symmetry_dataset.number)),
                "choice": str(symmetry_dataset.choice),
                "origin_shift": [
                    round(float(value), 8) for value in symmetry_dataset.origin_shift.tolist()
                ],
                "transformation_matrix": [
                    [round(float(value), 8) for value in row]
                    for row in np.array(symmetry_dataset.transformation_matrix).tolist()
                ],
                "std_rotation_matrix": [
                    [round(float(value), 8) for value in row]
                    for row in np.array(symmetry_dataset.std_rotation_matrix).tolist()
                ],
                "equivalent_atoms": [
                    int(value) for value in symmetry_dataset.equivalent_atoms.tolist()
                ],
                "wyckoffs": [str(value) for value in symmetry_dataset.wyckoffs],
            }
    _write_yaml(task_input.output, analysis)
    return {
        "task": "structure-info",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "formula": analysis["formula"],
        "natoms": analysis["natoms"],
        "volume": analysis["volume"],
        "cell_lengths": analysis["cell_lengths"],
        "cell_angles": analysis["cell_angles"],
        "symmetry_file_written": True,
        "spacegroup": analysis.get("symmetry", {}).get("international_symbol", "N/A"),
        "point_group": analysis.get("symmetry", {}).get("point_group", "N/A"),
        "crystal_system": analysis.get("symmetry", {}).get("crystal_system", "N/A"),
    }
