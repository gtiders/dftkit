from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import ase.io
import dpdata

from dftkit.schemas.abacus.file_conversion import PoscarToStruInput


def _load_basis_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("basis_json must contain a JSON object")

    result: dict[str, Any] = {}
    pp_file = payload.get("pp_file")
    if pp_file is not None:
        if not isinstance(pp_file, dict):
            raise ValueError("pp_file must be a JSON object")
        result["pp_file"] = {str(key): str(value) for key, value in pp_file.items()}

    numerical_orbital = payload.get("numerical_orbital")
    if numerical_orbital is not None:
        if not isinstance(numerical_orbital, dict):
            raise ValueError("numerical_orbital must be a JSON object")
        result["numerical_orbital"] = {
            str(key): str(value) for key, value in numerical_orbital.items()
        }

    return result


def run_poscar_to_stru_convert(task_input: PoscarToStruInput) -> dict[str, Any]:
    atoms = ase.io.read(task_input.input)

    basis_config = (
        _load_basis_config(task_input.basis_json)
        if task_input.basis_json is not None
        else {}
    )

    system = dpdata.System()
    system.from_ase_structure(atoms)

    kwargs: dict[str, Any] = {}
    if "pp_file" in basis_config:
        kwargs["pp_file"] = basis_config["pp_file"]
    if "numerical_orbital" in basis_config:
        kwargs["numerical_orbital"] = basis_config["numerical_orbital"]
    system.to_abacus_stru(task_input.output, **kwargs)

    # 5. 返回结果
    return {
        "task": "poscar-to-stru-convert",
        "input": str(task_input.input),
        "output": str(task_input.output),
        "basis_json": str(task_input.basis_json) if task_input.basis_json else "None",
        "has_pp_file": "pp_file" in basis_config,
        "has_numerical_orbital": "numerical_orbital" in basis_config,
    }
