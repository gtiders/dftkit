from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CutoffRadiiInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    source_type: Literal["file", "matrix"] | None = Field(default=None)
    supercell: Path | None = Field(default=Path("SPOSCAR"))
    matrix: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_source(self) -> "CutoffRadiiInput":
        if self.source_type is None:
            self.source_type = "matrix" if self.matrix else "file"

        if self.source_type == "matrix":
            if not self.matrix:
                raise ValueError("matrix is required when source_type=matrix")
            self.supercell = None
            return self

        if self.source_type == "file":
            self.matrix = None
            if self.supercell is None:
                self.supercell = Path("SPOSCAR")
            return self

        return self
