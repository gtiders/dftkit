from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import ase.io
import dpdata

from dftkit.schemas.vasp.file_conversion import StruToPoscarInput


def run_stru_to_poscar_convert(task_input: StruToPoscarInput) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(suffix=".vasp", delete=False) as tmp:
        tmp_poscar = Path(tmp.name)

    try:
        system = dpdata.System()
        system.from_abacus_stru(task_input.input)
        system.to_poscar(tmp_poscar)
        atoms = ase.io.read(tmp_poscar, format="vasp")
        ase.io.write(task_input.output, atoms, format="vasp")
    finally:
        if tmp_poscar.exists():
            tmp_poscar.unlink()

    return {
        "task": "stru-to-poscar-convert",
        "input": str(task_input.input),
        "output": str(task_input.output),
    }
