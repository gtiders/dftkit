from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


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
