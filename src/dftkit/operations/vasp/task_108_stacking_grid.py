from __future__ import annotations

from pathlib import Path

import numpy as np
from ase.io import read, write

from dftkit.schemas.vasp.structure_analysis import StackingGridInput

AXIS_TO_INDEX = {"a": 0, "b": 1, "c": 2}


def _output_poscar_path(
    output_root: Path,
    axis1: str,
    axis2: str,
    i1: int,
    i2: int,
) -> Path:
    return output_root / f"{axis1}{i1:02d}_{axis2}{i2:02d}" / "POSCAR"


def run_stacking_grid(task_input: StackingGridInput) -> dict[str, object]:
    axis_grids = {
        "a": task_input.a_grid,
        "b": task_input.b_grid,
        "c": task_input.c_grid,
    }
    normal_axis = next(axis for axis, grid in axis_grids.items() if grid == 0)
    shift_axes = [
        (axis, AXIS_TO_INDEX[axis], grid)
        for axis, grid in axis_grids.items()
        if grid > 0
    ]
    shift_axis1, shift_index1, grid1 = shift_axes[0]
    shift_axis2, shift_index2, grid2 = shift_axes[1]

    atoms = read(task_input.input, format="vasp")
    scaled = atoms.get_scaled_positions(wrap=True)

    normal_coord = scaled[:, AXIS_TO_INDEX[normal_axis]]
    near_cut = np.abs(normal_coord - task_input.cut) <= task_input.tol
    if np.any(near_cut):
        indices = ", ".join(str(int(index)) for index in np.where(near_cut)[0])
        raise ValueError(
            f"atoms are too close to cut={task_input.cut}: indices {indices}; "
            "choose a different cut or smaller tol"
        )

    if task_input.move == "upper":
        mask = normal_coord > task_input.cut
    else:
        mask = normal_coord < task_input.cut

    if not np.any(mask):
        raise ValueError(f"no atoms selected for move={task_input.move}; check cut")
    if np.all(mask):
        raise ValueError(f"all atoms selected for move={task_input.move}; check cut")

    output_root = task_input.output
    output_root.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    for i1 in range(grid1):
        for i2 in range(grid2):
            if task_input.skip_origin and i1 == 0 and i2 == 0:
                skipped += 1
                continue

            poscar_path = _output_poscar_path(output_root, shift_axis1, shift_axis2, i1, i2)
            if poscar_path.exists() and not task_input.overwrite:
                raise ValueError(
                    f"{poscar_path} already exists; use overwrite=true to replace it"
                )

            shifted = scaled.copy()
            shifted[mask, shift_index1] = (shifted[mask, shift_index1] + i1 / grid1) % 1.0
            shifted[mask, shift_index2] = (shifted[mask, shift_index2] + i2 / grid2) % 1.0

            new_atoms = atoms.copy()
            new_atoms.set_scaled_positions(shifted)
            poscar_path.parent.mkdir(parents=True, exist_ok=True)
            write(
                poscar_path,
                new_atoms,
                format="vasp",
                direct=True,
                vasp5=True,
                sort=False,
            )
            written += 1

    return {
        "task": "stacking-grid-generate",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "vacuum_axis": normal_axis,
        "shift_axes": [shift_axis1, shift_axis2],
        "grid_shape": [grid1, grid2],
        "cut": task_input.cut,
        "move": task_input.move,
        "selected_atoms": int(np.count_nonzero(mask)),
        "total_atoms": len(atoms),
        "written_poscars": written,
        "skipped_origin": skipped,
    }
