# API Reference

Complete API reference for the Abaqus-SwiftComp Toolset.

## Toolkit Icons Reference

The following icons are used throughout the GUI interface:

| Icon | Function | Description |
|------|----------|-------------|
| ![SG 1D](/_static/images/icons/sg_1d_small.png) | SG 1D | Generate 1D structural geometry |
| ![SG 2D UC](/_static/images/icons/sg_2d_uc_small.png) | SG 2D UC | Generate 2D unit cell |
| ![SG 2D Laminate](/_static/images/icons/sg_2d_laminate_small.png) | SG 2D Laminate | Generate 2D laminate structure |
| ![SG 3D](/_static/images/icons/sg_3d_small.png) | SG 3D | Generate 3D structural geometry |
| ![VABS](/_static/images/icons/vabs_small.png) | VABS | Run VABS analysis |
| ![SC Homo](/_static/images/icons/sc_homo_small.png) | SC Homo | SwiftComp homogenization |
| ![SC Dehomo](/_static/images/icons/sc_dehomo_small.png) | SC Dehomo | SwiftComp dehomogenization |
| ![Add Layups](/_static/images/icons/add_layups_small.png) | Add Layups | Define material layups |
| ![Node 9](/_static/images/icons/node_9_small.png) | Node 9 | 9-node element configuration |

## Core Modules

### abaqus_toolkit.core

The core module provides fundamental classes and functions.

```{eval-rst}
.. automodule:: abaqus_toolkit.core
   :members:
   :undoc-members:
   :show-inheritance:
```

### abaqus_toolkit.analysis

Analysis-related functionality.

```{eval-rst}
.. automodule:: abaqus_toolkit.analysis
   :members:
   :undoc-members:
   :show-inheritance:
```

## Classes

### AbaqusModel

```python
class AbaqusModel:
    """Main class for Abaqus model operations."""
    
    def __init__(self, model_name: str):
        """Initialize the model.
        
        Args:
            model_name: Name of the model
        """
        pass
    
    def create_part(self, name: str, dimensions: tuple):
        """Create a new part.
        
        Args:
            name: Part name
            dimensions: Part dimensions (x, y, z)
            
        Returns:
            Part object
        """
        pass
```

### SwiftCompAnalysis

```python
class SwiftCompAnalysis:
    """Interface for SwiftComp analysis."""
    
    def run_analysis(self, input_file: str) -> dict:
        """Run SwiftComp analysis.
        
        Args:
            input_file: Path to input file
            
        Returns:
            Analysis results dictionary
        """
        pass
```

## Functions

### Utility Functions

```python
def validate_input(input_data: dict) -> bool:
    """Validate input data structure.
    
    Args:
        input_data: Input data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    pass

def export_results(results: dict, format: str = "vtk"):
    """Export analysis results.
    
    Args:
        results: Results dictionary
        format: Output format ("vtk", "csv", "json")
    """
    pass
```

## Constants

```python
# Material property constants
STEEL_PROPERTIES = {
    "E": 200e9,  # Young's modulus (Pa)
    "nu": 0.3,   # Poisson's ratio
    "rho": 7850  # Density (kg/m³)
}

ALUMINUM_PROPERTIES = {
    "E": 70e9,
    "nu": 0.33,
    "rho": 2700
}
```

## Exceptions

```python
class AbaqusToolkitError(Exception):
    """Base exception for toolkit errors."""
    pass

class ModelError(AbaqusToolkitError):
    """Raised when model operations fail."""
    pass

class AnalysisError(AbaqusToolkitError):
    """Raised when analysis fails."""
    pass
```

## Examples

### Basic Usage

```python
from abaqus_toolkit import AbaqusModel, SwiftCompAnalysis

# Create model
model = AbaqusModel("my_model")

# Create part
part = model.create_part("beam", (10, 1, 1))

# Run analysis
analysis = SwiftCompAnalysis()
results = analysis.run_analysis("input.dat")
```

### Advanced Usage

```python
# Custom material properties
custom_material = {
    "E": 150e9,
    "nu": 0.25,
    "rho": 8000
}

# Apply material to part
part.assign_material(custom_material)

# Configure analysis
analysis.set_solver_options({
    "max_iterations": 1000,
    "tolerance": 1e-6
})
```
