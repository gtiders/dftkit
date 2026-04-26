from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class StruToPoscarInput(BaseModel):
    input: Path = Field(default=Path("STRU"))
    output: Path = Field(default=Path("POSCAR"))
