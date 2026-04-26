from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic import field_validator


class PoscarToStruInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("STRU"))
    basis_json: Path | None = Field(default=None)

    @field_validator("basis_json", mode="before")
    @classmethod
    def _normalize_empty_basis_json(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class PoscarToStruSwapACInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("STRU"))
    basis_json: Path | None = Field(default=None)

    @field_validator("basis_json", mode="before")
    @classmethod
    def _normalize_empty_basis_json(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value
