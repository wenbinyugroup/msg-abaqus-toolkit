# Reusing Images from Source Code in Documentation

This guide explains different methods to reuse images from your source code (like icons and diagrams) in your Sphinx documentation.

## Available Source Images

Your project has images in:
- `scripts/Icon/` - UI icons and small graphics
- `scripts/Image/` - Larger diagrams and interface screenshots

## Method 1: Copy to _static (Recommended for Most Cases)

### Advantages
- ✅ Simple and reliable
- ✅ Works on all platforms
- ✅ No permission issues
- ✅ Images are always available for documentation builds

### Implementation
Images have been copied to:
```
doc/source/_static/images/
├── icons/           # From scripts/Icon/
└── source_images/   # From scripts/Image/
```

### Usage Examples
```markdown
# Using icons inline
Click the ![add layups icon](/_static/images/icons/add_layups_small.png) button to add layups.

# Using larger images as figures
```{figure} /_static/images/source_images/i_beam.png
:alt: I-beam cross-section diagram
:width: 400px
:align: center

I-beam cross-section showing the structural geometry.
```
```

### Keeping Images Updated
Create a script to sync images when they change:

```powershell
# sync_images.ps1
Copy-Item "scripts\Icon\*" "doc\source\_static\images\icons\" -Force
Copy-Item "scripts\Image\*" "doc\source\_static\images\source_images\" -Force
Write-Host "Images synced successfully!"
```

## Method 2: Symbolic Links (Advanced)

### Advantages
- ✅ Always up-to-date with source
- ✅ No duplication of files
- ✅ Automatic sync

### Disadvantages
- ❌ Requires admin privileges on Windows
- ❌ May not work in all deployment environments
- ❌ Can break if source files move

### Implementation (Linux/Mac)
```bash
ln -s ../../../scripts/Icon doc/source/_static/images/icons
ln -s ../../../scripts/Image doc/source/_static/images/source_images
```

### Implementation (Windows - Admin Required)
```powershell
New-Item -ItemType SymbolicLink -Path "doc\source\_static\images\icons" -Target "scripts\Icon"
New-Item -ItemType SymbolicLink -Path "doc\source\_static\images\source_images" -Target "scripts\Image"
```

## Method 3: Sphinx Configuration (Advanced)

### Add to conf.py
```python
import os
import shutil

# Copy source images during build
def copy_source_images(app, config):
    source_icon_dir = os.path.join(app.srcdir, '..', '..', 'scripts', 'Icon')
    source_image_dir = os.path.join(app.srcdir, '..', '..', 'scripts', 'Image')
    
    target_icon_dir = os.path.join(app.srcdir, '_static', 'images', 'icons')
    target_image_dir = os.path.join(app.srcdir, '_static', 'images', 'source_images')
    
    if os.path.exists(source_icon_dir):
        shutil.copytree(source_icon_dir, target_icon_dir, dirs_exist_ok=True)
    
    if os.path.exists(source_image_dir):
        shutil.copytree(source_image_dir, target_image_dir, dirs_exist_ok=True)

def setup(app):
    app.connect('config-inited', copy_source_images)
```

## Method 4: Build Script Integration

### Create build_docs.py
```python
#!/usr/bin/env python3
import os
import shutil
import subprocess

def sync_images():
    """Copy images from source to documentation."""
    # Copy icons
    shutil.copytree('scripts/Icon', 'doc/source/_static/images/icons', dirs_exist_ok=True)
    # Copy images  
    shutil.copytree('scripts/Image', 'doc/source/_static/images/source_images', dirs_exist_ok=True)
    print("✅ Images synced")

def build_docs():
    """Build the documentation."""
    os.chdir('doc')
    result = subprocess.run(['make', 'html'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Documentation built successfully")
    else:
        print("❌ Documentation build failed")
        print(result.stderr)

if __name__ == "__main__":
    sync_images()
    build_docs()
```

## Usage Examples with Your Icons

### GUI Elements Documentation
```markdown
## User Interface Elements

The main toolbar contains several important buttons:

- ![SG 1D](/_static/images/icons/sg_1d_small.png) **SG 1D**: Generate 1D structural geometry
- ![SG 2D](/_static/images/icons/sg_2d_uc_small.png) **SG 2D**: Generate 2D unit cell
- ![SG 3D](/_static/images/icons/sg_3d_small.png) **SG 3D**: Generate 3D structural geometry
- ![VABS](/_static/images/icons/vabs_small.png) **VABS**: Run VABS analysis
- ![SwiftComp Homo](/_static/images/icons/sc_homo_small.png) **SC Homo**: SwiftComp homogenization
- ![SwiftComp Dehomo](/_static/images/icons/sc_dehomo_small.png) **SC Dehomo**: SwiftComp dehomogenization

### Workflow Steps

1. Click ![Add Layups](/_static/images/icons/add_layups_small.png) to define material layups
2. Use ![Node 9](/_static/images/icons/node_9_small.png) for 9-node element configuration
3. Access visualization with ![Visual](/_static/images/icons/sc_visual_small.png)
```

### Technical Diagrams
```markdown
## Cross-Section Types

The toolkit supports various cross-section geometries:

```{figure} /_static/images/source_images/i_beam.png
:alt: I-beam cross-section
:width: 300px
:align: center
:name: fig-ibeam

Standard I-beam cross-section geometry
```

```{figure} /_static/images/source_images/oblique_cs.png
:alt: Oblique coordinate system
:width: 300px
:align: center
:name: fig-oblique

Oblique coordinate system definition
```

## Interface Types

```{figure} /_static/images/source_images/HexInterface.png
:alt: Hexagonal interface
:width: 250px
:align: left

Hexagonal interface pattern
```

```{figure} /_static/images/source_images/squareInterface.png
:alt: Square interface
:width: 250px
:align: right

Square interface pattern
```
```

## Best Practices

1. **Organize by Type**: Keep icons and larger images in separate directories
2. **Consistent Naming**: Use descriptive names that match their function
3. **Size Appropriately**: Use small icons inline, larger images as figures
4. **Update Regularly**: Sync images when source code changes
5. **Document Usage**: Create a reference showing what each icon represents

## Automation Script

Here's a PowerShell script to automate image syncing:

```powershell
# File: sync_doc_images.ps1
Write-Host "Syncing documentation images..."

# Create directories if they don't exist
$iconDir = "doc\source\_static\images\icons"
$imageDir = "doc\source\_static\images\source_images"

if (!(Test-Path $iconDir)) { New-Item -ItemType Directory -Path $iconDir -Force }
if (!(Test-Path $imageDir)) { New-Item -ItemType Directory -Path $imageDir -Force }

# Copy files
Copy-Item "scripts\Icon\*" $iconDir -Force
Copy-Item "scripts\Image\*" $imageDir -Force

Write-Host "✅ Images synced successfully!"
Write-Host "Icons: $(Get-ChildItem $iconDir | Measure-Object).Count files"
Write-Host "Images: $(Get-ChildItem $imageDir | Measure-Object).Count files"
```

Run with: `.\sync_doc_images.ps1`
