from __future__ import annotations

from pathlib import Path
from typing import Any

from ase.io import read
import seekpath

from dftkit.schemas.vasp.kpath import KPathGenerateInput


def _render_kpath_text(code: str, path_data: dict[str, Any], line_density: int) -> str:
    lines = [
        f"# dftkit k-path for {code}",
        f"# line_density = {line_density}",
        "# points",
    ]
    for label, coords in sorted(path_data["point_coords"].items()):
        lines.append(
            f"{label:>8}  {coords[0]: .8f}  {coords[1]: .8f}  {coords[2]: .8f}"
        )
    lines.append("# path")
    for start, end in path_data["path"]:
        lines.append(f"{start} -> {end}")
    return "\n".join(lines) + "\n"


def run_kpath_generate(task_input: KPathGenerateInput) -> dict[str, Any]:
    atoms = read(task_input.input)
    cell = (
        atoms.cell.array,
        atoms.get_scaled_positions(),
        atoms.get_atomic_numbers(),
    )
    if task_input.primitive:
        path_data = seekpath.get_path(cell)
    else:
        path_data = seekpath.get_path_orig_cell(cell)
    rendered = _render_kpath_text(task_input.code, path_data, task_input.line_density)
    Path(task_input.output).write_text(rendered, encoding="utf-8")
    return {
        "task": "kpath-generate",
        "input": str(task_input.input),
        "code": task_input.code,
        "line_density": task_input.line_density,
        "primitive": task_input.primitive,
        "output": str(task_input.output),
        "segments": [f"{start}->{end}" for start, end in path_data["path"]],
        "point_count": len(path_data["point_coords"]),
    }
