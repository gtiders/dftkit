# AGENTS.md

## Purpose

This repository uses a strict three-layer architecture:

- `providers`: task registration
- `schemas`: validated task input models
- `operations`: task execution logic

The goal is clear ownership, predictable layout, and low coupling between menu registration, input validation, and task execution.

---

## Core Architecture

### Providers

Path:

- `src/dftkit/providers/`

Responsibilities:

- define provider-level `GROUP_NAMES`
- register tasks
- bind task id to schema model and operation function
- define prompt metadata
- keep tiny parser helpers only when necessary for prompt conversion

Must not contain:

- task business logic
- file I/O workflow logic
- structure transformation logic
- large validation logic
- heavy computational code

Rule:

- one provider, one file
- filename pattern: `<provider>.py`

Examples:

- `vasp.py`
- `abacus.py`

---

### Operations

Path:

- `src/dftkit/operations/<provider>/`

Responsibilities:

- implement the actual task behavior
- read input files
- run domain logic
- write outputs
- return structured result summaries
- call execution-layer libraries such as `dpdata`, `ASE`, `spglib`, or similar dependencies when needed

Rules:

- one concrete task id, one operation module
- this is mandatory
- task implementations must not use cross-task shared implementation modules
- if a task is simple, use one file
- if a task is genuinely large, use a dedicated package directory for that single task only

Allowed task module patterns:

- `task_<task_id>_<task_slug>.py`
- `task_<task_id>_<task_slug>/`

Examples:

- `task_001_kpoints_mesh.py`
- `task_002_band_kpoints_prepare.py`
- `task_108_stacking_grid.py`
- `task_205_complex_surface_workflow/`

If a task uses a directory module, the directory name must follow the exact same naming rule:

- `task_<task_id>_<task_slug>/`

That task directory may contain private helper files only for that task.
Those helpers must not be imported by any other task.

Forbidden:

- `_shared.py`
- `_io.py`
- `_geometry.py`
- any other cross-task helper module under `operations/<provider>/`

Public function naming:

- `run_<task_slug>`

Examples:

- `run_kpoints_mesh`
- `run_band_kpoints_prepare`
- `run_stacking_grid`

Each task module should expose exactly one public runner.
Private helper functions may exist only inside that task file or inside that task's own directory package.

---

### Schemas

Path:

- `src/dftkit/schemas/<provider>/`

Responsibilities:

- define validated task input models
- normalize user input into stable internal data
- enforce input-level validation only

Must not contain:

- task execution logic
- file reading or writing
- provider registration logic
- workflow library imports or calls such as `dpdata`, `ASE`, `spglib`, or similar execution-layer dependencies

Rules:

- schemas are organized by first-level menu, not by task id
- one first-level menu, one schema file
- this is mandatory

Filename pattern:

- `<group_slug>.py`

Examples for VASP:

- `input_files.py`
- `structure_analysis.py`
- `file_conversion.py`
- `electronic_structure.py`
- `kpath_brillouin_zone.py`

Model naming:

- `<TaskSlug>Input`

Examples:

- `KpointsMeshInput`
- `BandKpointsPrepareInput`
- `StackingGridInput`

A schema file may contain multiple input models for tasks that belong to the same first-level menu.

---

## Workflow Library Rule

Do not use workflow libraries directly in `schemas`.

This is mandatory.

Rules:

- `schemas` define validated inputs only
- `providers` register tasks only
- workflow libraries such as `dpdata`, `ASE`, `spglib`, or similar dependencies may only be used in `operations`

This rule exists to keep schema models lightweight, stable, low-side-effect, and independent from execution-layer dependencies.

---

## Task Mapping Rule

Task ids and schema files represent different dimensions and must not be mixed:

- task id = unit of execution
- first-level menu = unit of schema grouping

Therefore:

- each task id owns one operation module
- each first-level menu owns one schema file

This rule is mandatory.

---

## Import Safety Rule

Python module paths must use identifier-safe names.

Therefore, filenames that start directly with digits are forbidden for importable modules.

Forbidden:

- `001_kpoints_mesh.py`
- `108_stacking_grid.py`

Required:

- `task_001_kpoints_mesh.py`
- `task_108_stacking_grid.py`

This rule exists to keep imports valid and predictable.

---

## Provider Registration Rule

Provider files must only register tasks and connect the layers.

A provider file should answer only:

- what tasks exist
- which menu each task belongs to
- which schema validates the task
- which operation executes the task

It must not implement the task itself.

---

## Planning Approval Rule

Before implementing any new task or significantly refactoring an existing task, the agent must first present a concrete implementation plan and ask the developer for approval.

This is mandatory.

The plan must include at least:

- task id
- task slug
- target provider
- target first-level menu
- target schema file
- target operation module
- public runner name
- input design
- output design
- whether the task will be a single file or a task directory package
- boundary and reuse relationship with existing tasks

Implementation must not begin until the developer explicitly approves the plan.

---

## Adding a New Task

When adding a new task, all of the following are required:

1. Create a dedicated operation module:
   - `src/dftkit/operations/<provider>/task_<task_id>_<task_slug>.py`
   - or `src/dftkit/operations/<provider>/task_<task_id>_<task_slug>/`

2. Add the input model to the correct first-level menu schema file:
   - `src/dftkit/schemas/<provider>/<group_slug>.py`

3. Register the task in:
   - `src/dftkit/providers/<provider>.py`

4. Add tests:
   - `tests/test_<provider>_<task_id>_<task_slug>.py`

A task is not complete unless all four layers are updated consistently.

---

## Directory Responsibilities

### `src/dftkit/providers/`

Purpose:

- expose provider-specific task catalogs
- bind task metadata to schema and operation

### `src/dftkit/schemas/<provider>/`

Purpose:

- define validated input models grouped by first-level menu

### `src/dftkit/operations/<provider>/`

Purpose:

- implement each concrete task in its own dedicated module

### `src/dftkit/registry.py`

Purpose:

- collect and expose provider definitions only

It should remain thin.

### `tests/`

Purpose:

- validate task behavior
- prefer one test module per task

Filename pattern:

- `test_<provider>_<task_id>_<task_slug>.py`

Examples:

- `test_vasp_001_kpoints_mesh.py`
- `test_vasp_108_stacking_grid.py`

---

## File Cohesion Rules

### Providers

Provider files may be large because they hold task metadata, but they must remain registration-only files.

If parser helpers become numerous, move them into a small provider-local helper module.

### Schemas

Schema files must stay cohesive around one first-level menu.

If a schema file becomes too large, split only by explicit subdomain, not by task id.

Example:

- `structure_analysis_core.py`
- `structure_analysis_surface.py`

Do not split schemas by task id unless the repository-wide architecture rule is intentionally changed.

### Operations

Operation code must remain task-scoped.

Do not create any cross-task implementation sharing layer.

If a task is complex:

- keep it in one file if still readable
- otherwise convert it into a dedicated task directory package using the same `task_<task_id>_<task_slug>` naming rule

Any helper code inside that directory belongs only to that task and must not be reused by other tasks.

---

## Example Layout

Example VASP target layout:

```text
src/dftkit/providers/
  vasp.py

src/dftkit/schemas/vasp/
  input_files.py
  structure_analysis.py
  file_conversion.py
  electronic_structure.py
  kpath_brillouin_zone.py

src/dftkit/operations/vasp/
  task_001_kpoints_mesh.py
  task_002_band_kpoints_prepare.py
  task_102_structure_info.py
  task_103_primitive_standardize.py
  task_104_conventional_standardize.py
  task_105_supercell_build.py
  task_106_cutoff_radii.py
  task_108_stacking_grid.py
```

---

## Review Checklist

Every new task should be reviewed against these questions:

- does the provider only register the task
- does the schema live in the correct first-level menu file
- does the task have its own dedicated operation module
- is the operation module import-safe
- is there exactly one clear public runner
- are workflow libraries kept out of schemas
- is there no cross-task shared implementation module
- was the implementation plan approved before coding began
- are tests named and scoped correctly

---

## Non-Negotiable Rules

- one concrete task id, one operation module
- one first-level menu, one schema file
- providers contain registration only
- schemas contain input models and validation only
- operations contain execution logic only
- operation modules must be import-safe
- workflow libraries must not be used in schema files
- task business logic must not live in provider files
- cross-task shared implementation modules are forbidden
- implementation must not begin before the developer approves the plan
