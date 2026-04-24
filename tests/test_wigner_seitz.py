from __future__ import annotations

import pytest
from ase import Atoms
from ase.units import Bohr

from dftkit.operations.vasp.cutoff import analyze_real_space_wigner_seitz


@pytest.mark.parametrize(
    ("cell", "expected"),
    [
        ([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]], 1.0),
        ([[1.0, 0.0, 0.0], [0.5, 0.8660254, 0.0], [0.0, 0.0, 5.0]], 0.5),
    ],
)
def test_wigner_seitz_inradius_matches_half_of_shortest_lattice_vector(cell, expected):
    atoms = Atoms("H", cell=cell, scaled_positions=[[0.0, 0.0, 0.0]], pbc=True)
    analysis = analyze_real_space_wigner_seitz(atoms)

    assert analysis["inradius"] == pytest.approx(expected, abs=1e-8)
    assert analysis["inradius_bohr"] == pytest.approx(expected / Bohr, abs=1e-8)
