from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class KpointsMeshInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("KPOINTS"))
    mode: str = Field(default="gamma")
    kpr: float = Field(default=0.04, gt=0.0)

    @field_validator("mode")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        mapping = {
            "1": "gamma",
            "gamma": "gamma",
            "g": "gamma",
            "2": "monkhorst-pack",
            "monkhorst-pack": "monkhorst-pack",
            "monkhorst": "monkhorst-pack",
            "mp": "monkhorst-pack",
            "m": "monkhorst-pack",
        }
        if normalized not in mapping:
            raise ValueError("mode must be gamma or monkhorst-pack")
        return mapping[normalized]


class BandPathInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("KPOINTS"))
    kpath_output: Path = Field(default=Path("kpath.yaml"))
    line_density: int = Field(default=20, ge=1)
