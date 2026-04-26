from __future__ import annotations

from pathlib import Path

import pytest
from ase import Atoms
from ase.io import read
from ase.io.vasp import write_vasp

from dftkit.operations.vasp.task_112_bilayer_build import run_bilayer_build
from dftkit.schemas.vasp.structure_analysis import BilayerBuildInput


def _write_graphene_monolayer(path: Path) -> None:
    graphene = Atoms(
        "C2",
        cell=[
            [2.46, 0.0, 0.0],
            [1.23, 2.1304224933, 0.0],
            [0.0, 0.0, 20.0],
        ],
        positions=[
            [0.0, 0.0, 10.0],
            [1.23, 0.7101408311, 10.0],
        ],
        pbc=[True, True, True],
    )
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, graphene, direct=False, sort=False)


def _write_thick_monolayer(path: Path) -> None:
    thick_layer = Atoms(
        "C2",
        cell=[
            [2.46, 0.0, 0.0],
            [1.23, 2.1304224933, 0.0],
            [0.0, 0.0, 20.0],
        ],
        positions=[
            [0.0, 0.0, 2.0],
            [1.23, 0.7101408311, 18.0],
        ],
        pbc=[True, True, True],
    )
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, thick_layer, direct=False, sort=False)


def _write_mixed_monolayer(path: Path) -> None:
    mixed_layer = Atoms(
        ["O", "C"],
        cell=[
            [2.46, 0.0, 0.0],
            [1.23, 2.1304224933, 0.0],
            [0.0, 0.0, 20.0],
        ],
        positions=[
            [0.0, 0.0, 10.2],
            [1.23, 0.7101408311, 9.8],
        ],
        pbc=[True, True, True],
    )
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, mixed_layer, direct=False, sort=False)


def test_bilayer_build_duplicates_graphene_and_centers_it_along_z(tmp_path: Path):
    input_path = tmp_path / "POSCAR"
    output_path = tmp_path / "BPOSCAR"
    _write_graphene_monolayer(input_path)

    result = run_bilayer_build(BilayerBuildInput(input=input_path, output=output_path))
    bilayer = read(output_path, format="vasp")
    z_positions = bilayer.get_positions()[:, 2]

    assert result["gap"] == pytest.approx(3.5, abs=1e-8)
    assert result["natoms_monolayer"] == 2
    assert result["natoms_bilayer"] == 4
    assert bilayer.cell[2, 2] == pytest.approx(30.0, abs=1e-8)
    assert result["interlayer_gap"] == pytest.approx(3.5, abs=1e-8)
    assert result["bilayer_center_z"] == pytest.approx(15.0, abs=1e-8)
    assert (float(z_positions.min()) + float(z_positions.max())) / 2.0 == pytest.approx(
        15.0, abs=1e-8
    )


def test_bilayer_build_sorts_species_in_output_poscar(tmp_path: Path):
    input_path = tmp_path / "POSCAR"
    output_path = tmp_path / "BPOSCAR"
    _write_mixed_monolayer(input_path)

    run_bilayer_build(BilayerBuildInput(input=input_path, output=output_path))

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert lines[5].split() == ["C", "O"]
    assert lines[6].split() == ["2", "2"]


def test_bilayer_build_rejects_z_length_below_minimum():
    with pytest.raises(ValueError, match="z_length must be at least 30.0"):
        BilayerBuildInput(z_length=29.0)


def test_bilayer_build_rejects_when_requested_z_length_is_too_short(tmp_path: Path):
    input_path = tmp_path / "POSCAR"
    _write_thick_monolayer(input_path)

    with pytest.raises(ValueError, match="bilayer height exceeds requested z_length"):
        run_bilayer_build(
            BilayerBuildInput(
                input=input_path,
                output=tmp_path / "BPOSCAR",
                gap=3.5,
                z_length=30.0,
            )
        )
