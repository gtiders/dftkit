from __future__ import annotations

from typing import Any

import numpy as np
from ase import Atoms
from ase.io import read
from ase.io.vasp import write_vasp

from dftkit.schemas.vasp.structure_analysis import BilayerBuildInput


def _write_poscar(path, atoms: Atoms) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, atoms, direct=True, sort=True)


def run_bilayer_build(task_input: BilayerBuildInput) -> dict[str, Any]:
    monolayer = read(task_input.input, format="vasp")
    positions = monolayer.get_positions()
    z_positions = positions[:, 2]
    z_min = float(np.min(z_positions))
    z_max = float(np.max(z_positions))
    thickness = z_max - z_min
    bilayer_height = 2.0 * thickness + task_input.gap

    if bilayer_height >= task_input.z_length:
        raise ValueError(
            "bilayer height exceeds requested z_length: "
            f"monolayer_thickness={thickness:.8f}, "
            f"gap={task_input.gap:.8f}, "
            f"required_min_z_length>{bilayer_height:.8f}, "
            f"requested_z_length={task_input.z_length:.8f}"
        )

    local_positions = positions.copy()
    local_positions[:, 2] -= z_min

    bottom_positions = local_positions.copy()
    top_positions = local_positions.copy()
    top_positions[:, 2] += thickness + task_input.gap

    centered_shift = (task_input.z_length - bilayer_height) / 2.0
    bottom_positions[:, 2] += centered_shift
    top_positions[:, 2] += centered_shift

    bilayer_positions = np.vstack([bottom_positions, top_positions])
    cell = np.array(monolayer.cell)
    cell[2] = np.array([0.0, 0.0, task_input.z_length])

    bilayer = Atoms(
        symbols=list(monolayer.symbols) + list(monolayer.symbols),
        positions=bilayer_positions,
        cell=cell,
        pbc=monolayer.pbc,
    )
    _write_poscar(task_input.output, bilayer)

    bottom_zmax = float(np.max(bottom_positions[:, 2]))
    top_zmin = float(np.min(top_positions[:, 2]))
    bilayer_center_z = (float(np.min(bilayer_positions[:, 2])) + float(np.max(bilayer_positions[:, 2]))) / 2.0

    return {
        "task": "bilayer-build",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "gap": task_input.gap,
        "z_length": task_input.z_length,
        "vacuum_axis": "z",
        "natoms_monolayer": len(monolayer),
        "natoms_bilayer": len(bilayer),
        "monolayer_thickness": thickness,
        "bilayer_height": bilayer_height,
        "bottom_top_zmax": bottom_zmax,
        "top_bottom_zmin": top_zmin,
        "interlayer_gap": top_zmin - bottom_zmax,
        "bilayer_center_z": bilayer_center_z,
        "box_center_z": task_input.z_length / 2.0,
        "atom_order": "sorted-by-species",
    }
