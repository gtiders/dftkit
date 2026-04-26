from __future__ import annotations

from pathlib import Path

from dftkit.schemas.abacus.file_conversion import (
    PoscarToStruInput,
    PoscarToStruSwapACInput,
)


def test_poscar_to_stru_input_treats_blank_basis_json_as_none() -> None:
    task_input = PoscarToStruInput.model_validate({"basis_json": ""})

    assert task_input.basis_json is None


def test_poscar_to_stru_swap_ac_input_treats_blank_basis_json_as_none() -> None:
    task_input = PoscarToStruSwapACInput.model_validate({"basis_json": "   "})

    assert task_input.basis_json is None


def test_poscar_to_stru_input_keeps_non_empty_basis_json_path() -> None:
    task_input = PoscarToStruInput.model_validate({"basis_json": "basis.json"})

    assert task_input.basis_json == Path("basis.json")
