from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class KPathGenerateInput(BaseModel):
    input: Path
    code: str = Field(default="vasp")
    line_density: int = Field(default=20, ge=1)
    primitive: bool = Field(default=True)
    output: Path = Field(default=Path("KPOINTS"))

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("code cannot be empty")
        return normalized
