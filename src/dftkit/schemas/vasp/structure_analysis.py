from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class StructureInfoInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    format: str = Field(default="vasp")
    symmetry: bool = Field(default=True)
    output: Path = Field(default=Path("symmetry.yaml"))

    @field_validator("format")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        return normalized or "vasp"


class PrimitiveStandardizeInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("PPOSCAR"))
    symprec: float = Field(default=1e-5)
    angle_tolerance: float = Field(default=-1.0)


class ConventionalStandardizeInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("CPOSCAR"))
    symprec: float = Field(default=1e-5)
    angle_tolerance: float = Field(default=-1.0)


class SupercellBuildInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    output: Path = Field(default=Path("SPOSCAR"))
    matrix: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]

    @field_validator("matrix", mode="before")
    @classmethod
    def normalize_matrix(cls, value: object):
        if isinstance(value, str):
            tokens = value.replace(",", " ").replace(";", " ").split()
            numbers = [int(token) for token in tokens]
        elif isinstance(value, (list, tuple)):
            flat: list[int] = []
            for item in value:
                if isinstance(item, (list, tuple)):
                    flat.extend(int(entry) for entry in item)
                else:
                    flat.append(int(item))
            numbers = flat
        else:
            raise ValueError("matrix must be a string or integer sequence")

        if len(numbers) == 3:
            a, b, c = numbers
            return ((a, 0, 0), (0, b, 0), (0, 0, c))
        if len(numbers) == 9:
            return (
                (numbers[0], numbers[1], numbers[2]),
                (numbers[3], numbers[4], numbers[5]),
                (numbers[6], numbers[7], numbers[8]),
            )
        raise ValueError("matrix must contain either 3 or 9 integers")


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


class StackingGridInput(BaseModel):
    input: Path = Field(default=Path("POSCAR"))
    a_grid: int = Field(default=0)
    b_grid: int = Field(default=0)
    c_grid: int = Field(default=0)
    output: Path = Field(default=Path("stacking_grid"))
    cut: float = Field(default=0.5)
    move: str = Field(default="upper")
    tol: float = Field(default=1e-6)
    skip_origin: bool = Field(default=False)
    overwrite: bool = Field(default=False)

    @field_validator("move")
    @classmethod
    def normalize_move(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"upper", "lower"}:
            raise ValueError("move must be either 'upper' or 'lower'")
        return normalized

    @model_validator(mode="after")
    def validate_grids(self) -> "StackingGridInput":
        axis_grids = {"a": self.a_grid, "b": self.b_grid, "c": self.c_grid}
        negative_axes = [axis for axis, grid in axis_grids.items() if grid < 0]
        if negative_axes:
            axes = ", ".join(negative_axes)
            raise ValueError(f"grid values cannot be negative: {axes}")

        zero_axes = [axis for axis, grid in axis_grids.items() if grid == 0]
        if len(zero_axes) != 1:
            raise ValueError(
                "exactly one of a_grid, b_grid, c_grid must be 0 to mark the vacuum axis"
            )

        if not 0.0 < self.cut < 1.0:
            raise ValueError("cut must be between 0 and 1")
        if self.tol < 0.0:
            raise ValueError("tol must be non-negative")

        return self
