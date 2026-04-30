# AGENTS.md

## Project Overview

MSG-Abaqus Toolkit is an **Abaqus/CAE plugin** integrating SwiftComp and VABS for multiscale composite analysis using the Mechanics of Structure Genome (MSG) theory. The scripts run inside Abaqus's Python interpreter (not standalone), using the **AFX GUI framework** (Abaqus Foundation Extensions).

Documentation: https://wenbinyugroup.github.io/msg-abaqus-toolkit

## Product Direction

The current project goal is to act as the **Abaqus plugin shell layer** around the MSG workflows, not to remain the long-term home of SG/CS file-format business logic.

For new development, prefer this direction:

- Keep Abaqus/CAE integration here: AFX dialogs, command wiring, model/job export, workflow orchestration, external solver invocation, and visualization hooks.
- Gradually extract SG/CS data parsing, normalization, format conversion, and solver input/output serialization into reusable libraries such as `sgio`.
- Avoid adding new standalone Abaqus `.inp` parsing or SG/VABS/SwiftComp file writers here when equivalent logic belongs in the shared I/O layer.
- When touching an existing mixed-responsibility module, bias changes toward making this repository thinner at the boundary instead of deepening business logic inside the plugin.

The intended end state is:

- `msg-abaqus-toolkit`: Abaqus-specific UI/orchestration shell
- shared SG/CS I/O library: authoritative implementation of format semantics and conversion

## First Principles

Use first-principles thinking. Do not assume that I always clearly understand what I want or how to achieve it. Stay cautious and start from the fundamental needs and problems. If the motivation or goal is unclear, stop and discuss it with me.

## Development Commands

```bash
# Create virtual environment and install dependencies (docs only)
uv sync

# Build documentation
uv run sphinx-build -M html doc/source doc/build
```

The `pyproject.toml` dependencies are for documentation tooling only. The plugin scripts themselves run inside Abaqus's bundled Python environment and cannot be run standalone.

## Code Architecture

### Active vs Legacy

`scripts/py3/` is the active codebase (Python 3, Abaqus 2023+). `scripts/py2/` is legacy and should not be modified.

Within `scripts/py3/`, responsibilities are now split more explicitly:

- `main/` — Abaqus workflow entry points and high-level orchestration
- `dialogs/` / `forms/` — AFX GUI definitions and dialog behavior
- `sg/` — SG geometry/model creation logic
- `sgdataio/` — current SG-related SwiftComp/VABS data read/write and file parsing; treat this as an extraction target when logic can move into shared libraries
- `utils/` — shared helpers plus legacy Abaqus `.inp` parsing/reorganization utilities; do not grow this parsing layer unless there is no shared-library path

### Module Naming Convention

Nearly every feature follows a three-file pattern:

| Suffix | Role |
|--------|------|
| `*Form.py` | AFX GUI dialog definition (widgets, layout) |
| `*DB.py` | Dialog box logic (validation, data extraction, calling Main) |
| `*Main.py` | Core computation/Abaqus scripting logic |

### Entry Points

- **`SwiftCompGUI.py`** — AFX app initialization; registers `scCaeMainWindow`
- **`scCaeMainWindow.py`** — Main window; adds Abaqus standard modules plus the SwiftComp toolset
- **`scToolsetGui.py`** — Defines the persistent toolbar (12 buttons) pointing to all Form dialogs

### Analysis Pipeline

```
SG Creation
    main/: Abaqus-side SG creation workflows
    sg/: reusable SG geometry/model builders
    ↓
Homogenization
    main/: workflow orchestration for CAE and input-file paths
    sgdataio/swiftcomp.py: SwiftComp input serialization
    ↓  [invokes SwiftComp/VABS externally]
Result Parsing
    sgdataio/swiftcomp.py / sgdataio/vabs.py
    ↓
Macro Property Import
    main/scMacroMat.py + sgdataio/sgmodel.py
    ↓
Dehomogenization
    main/scLocalMain.py + sgdataio/swiftcomp.py
    ↓
Visualization
    main/scVisualMain.py / main/vabsVisualMain.py
```

### Key Large Files

- `sg2DAirfoil.py` (~65 KB) — Airfoil cross-section geometry generation
- `sg2DV5Main.py` (~50 KB) — 2D periodic unit cell creation
- `scVisualMain.py` (~47 KB) — All result visualization logic
- `scLocalDB.py` (~27 KB) — Dehomogenization dialog data handling
- `convert2sc.py` (~19 KB) — Format conversion to SwiftComp input

### Utility Modules

- `utilities.py` / `utilities_abq.py` — String formatting and Abaqus-specific helpers
- `parseAbaqusInput.py` / `readAbaqusInput.py` / `reorgAbaqusInput.py` — Abaqus `.inp` file parsing pipeline
- `UdetermineNSG.py` / `UdetermineVolume.py` — SG geometry introspection

### SG Data I/O

- `sgdataio/swiftcomp.py` — SwiftComp input writing, material serialization, result-file parsing, `.k` property parsing, and `.glb` writing
- `sgdataio/vabs.py` — VABS input writing, recovery input writing, and VABS result-file parsing
- `sgdataio/sgmodel.py` — SG model metadata/path resolution shared by localization and macro-property workflows

These modules are still active, but they should be treated as transitional ownership. If the same semantics are being implemented or consolidated in `sgio`, prefer moving toward the shared implementation and leaving only Abaqus-facing adapters here.

### VABS Parallel Path

`vabsForm/DB/Main.py`, `vabsVisualForm/DB/Main.py`, and `VABSGUI.py` / `vabsCaeMainWindow.py` mirror the SwiftComp flow for VABS integration. The VABS file-generation and result-parsing logic lives in `sgdataio/vabs.py`, while `createVABSInputMain.py` and `vabsMain.py` remain the Abaqus-side orchestration layer.


## Code Style Guidelines

- Encourage **modularity** and **reusability** in code design.
- Discourage **monolithic** code design.
- Avoid one giant function/file.
- When creating new functions, classes, modules, etc., start from simplest possible implementation, and gradually add features. **Do not overengineer**.
- Always use numpy style docstrings.
- Use comments to annotate key steps in the code.

- When developing new functions, make use of existing functions as much as possible. Try to avoid reinventing the wheel.

- When proposing modifications or refactoring plans, you must follow these rules:
  - Do not provide compatibility or workaround-based solutions.
  - Avoid over-engineering; follow the shortest path to implementation while still adhering to the first-principles requirement.
  - Do not introduce solutions beyond the requirements I provided (e.g., fallback or downgrade strategies), as they may cause deviations in business logic.
  - Ensure the logical correctness of the solution; it must be validated through end-to-end reasoning.



## Testing

There are no automated tests. The `tests/` directory contains Abaqus `.cae` models and SwiftComp output artifacts from manual integration testing. Verification requires running workflows inside Abaqus/CAE.
