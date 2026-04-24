from __future__ import annotations

from pathlib import Path

import pytest
from ase import Atoms
from ase.io.vasp import write_vasp
from ase.units import Bohr

from dftkit.operations.vasp.cutoff import run_cutoff_radii
from dftkit.schemas.vasp.cutoff import CutoffRadiiInput


def test_cutoff_radii_uses_wigner_seitz_inradius_for_maximum_cutoff(tmp_path: Path):
    primitive = Atoms(
        "H",
        cell=[[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]],
        scaled_positions=[[0.0, 0.0, 0.0]],
        pbc=True,
    )
    primitive_path = tmp_path / "POSCAR"
    with primitive_path.open("w", encoding="utf-8", newline="\n") as handle:
        write_vasp(handle, primitive, direct=True, sort=True)

    result = run_cutoff_radii(
        CutoffRadiiInput(input=primitive_path, supercell=None, matrix="2 1 1")
    )

    assert result["maximum_cutoff_radius"] == pytest.approx(1.5, abs=1e-8)
    assert result["maximum_cutoff_radius_bohr"] == pytest.approx(1.5 / Bohr, abs=1e-8)
    assert result["neighbor_cutoff_radii"] == []
