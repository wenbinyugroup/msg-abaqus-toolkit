# AGENTS.md

## Project Overview

MSG-Abaqus Toolkit is an **Abaqus/CAE plugin** integrating SwiftComp and VABS for multiscale composite analysis using the Mechanics of Structure Genome (MSG) theory. The scripts run inside Abaqus's Python interpreter (not standalone), using the **AFX GUI framework** (Abaqus Foundation Extensions).

Documentation: https://wenbinyugroup.github.io/msg-abaqus-toolkit

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
SG Creation (sg1D/2D/3DMain.py)
    ↓
Homogenization (scHomoMain.py → scGenInput.py → createSCInputMain.py → writeSCinput.py)
    ↓  [invokes SwiftComp/VABS externally]
Import Results (importSCMain.py)
    ↓
Macro Properties (scMacroMain.py)
    ↓
Dehomogenization (scLocalMain.py)
    ↓
Visualization (scVisualMain.py)
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
- `UdetermineNSG.py` / `UdetermineVolume.py` / `Usgmodel_info.py` — SG geometry introspection

### VABS Parallel Path

`vabsForm/DB/Main.py`, `vabsVisualForm/DB/Main.py`, and `VABSGUI.py` / `vabsCaeMainWindow.py` mirror the SwiftComp flow for VABS integration.


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
