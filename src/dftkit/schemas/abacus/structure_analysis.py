from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class StructureInfoInput(BaseModel):
    input: Path = Field(default=Path("STRU"))
    format: str = Field(default="auto")
    symmetry: bool = Field(default=True)
    output: Path = Field(default=Path("symmetry.yaml"))

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        return normalized or "auto"
