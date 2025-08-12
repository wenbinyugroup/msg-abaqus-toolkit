# Image Usage Guide for Sphinx Documentation

This guide explains how to properly organize and reference images in your Sphinx documentation with MyST-Parser.

## Directory Structure

All images should be placed in the `doc/source/_static/` directory with the following recommended organization:

```
doc/source/_static/
├── images/
│   ├── screenshots/     # GUI screenshots, interface images
│   ├── diagrams/        # Workflow diagrams, flowcharts
│   ├── logos/          # Company/project logos
│   ├── icons/          # Small icons and symbols
│   └── plots/          # Graphs, charts, analysis results
├── css/               # Custom CSS files
└── js/                # Custom JavaScript files
```

## Image Formats

Recommended formats:
- **PNG** - Best for screenshots, diagrams with text
- **JPG/JPEG** - Good for photographs, complex images
- **SVG** - Best for logos, simple diagrams (scalable)
- **GIF** - For simple animations (use sparingly)

## Referencing Images in Markdown

### 1. Standard Markdown Syntax
```markdown
![Alt text](/_static/images/screenshots/main_window.png)
```

### 2. MyST Image Directive (Recommended)
```markdown
```{image} /_static/images/diagrams/workflow.png
:alt: Workflow diagram showing the analysis process
:width: 600px
:align: center
```
```

### 3. Figure with Caption
```markdown
```{figure} /_static/images/screenshots/gui_interface.png
:alt: Main GUI interface
:width: 80%
:align: center
:name: fig-gui-interface

The main GUI interface showing all available tools and options.
```
```

### 4. Inline Images
```markdown
Click the ![settings icon](/_static/images/icons/settings.png) to open settings.
```

## Image Options

### Size Control
```markdown
```{image} /_static/images/diagram.png
:width: 400px          # Fixed width in pixels
:width: 80%            # Percentage of container width
:height: 300px         # Fixed height
:scale: 50%            # Scale percentage
```
```

### Alignment
```markdown
```{image} /_static/images/logo.png
:align: left           # left, center, right
```
```

### Advanced Options
```markdown
```{figure} /_static/images/complex_diagram.png
:alt: Complex analysis diagram
:width: 100%
:align: center
:name: fig-complex-analysis
:class: custom-image-class

This diagram shows the complete analysis workflow with all intermediate steps.
```
```

## Cross-Referencing Images

### Reference by Name
```markdown
As shown in {numref}`fig-gui-interface`, the interface provides...

See {ref}`fig-complex-analysis` for details.
```

### Reference with Custom Text
```markdown
The [main interface](fig-gui-interface) allows users to...
```

## Best Practices

### 1. File Naming
- Use descriptive names: `main_gui_window.png` not `image1.png`
- Use underscores or hyphens: `workflow_diagram.png`
- Include version if needed: `gui_v2_settings.png`

### 2. Image Quality
- Use high resolution for screenshots (at least 1920px wide)
- Optimize file sizes (use tools like TinyPNG)
- Ensure text in images is readable

### 3. Alt Text
- Always provide descriptive alt text
- Describe what the image shows, not just "image" or "screenshot"
- Keep it concise but informative

### 4. Captions
- Use captions to explain the context
- Reference specific elements in the image
- Keep captions under the image

## Examples for Different Use Cases

### Screenshots
```markdown
```{figure} /_static/images/screenshots/analysis_results.png
:alt: Analysis results window showing stress distribution
:width: 90%
:align: center
:name: fig-analysis-results

Analysis results window displaying the stress distribution across the model.
```
```

### Diagrams
```markdown
```{figure} /_static/images/diagrams/data_flow.png
:alt: Data flow diagram from input to output
:width: 70%
:align: center
:name: fig-data-flow

Data flow diagram showing how input files are processed to generate results.
```
```

### Logos and Branding
```markdown
```{image} /_static/images/logos/company_logo.svg
:alt: Company logo
:width: 200px
:align: right
:class: logo
```
```

### Mathematical Plots
```markdown
```{figure} /_static/images/plots/convergence_study.png
:alt: Convergence study showing error vs mesh density
:width: 80%
:align: center
:name: fig-convergence

Convergence study results showing the relationship between mesh density and solution accuracy.
```
```

## Troubleshooting

### Common Issues

1. **Image not displaying**
   - Check file path (use forward slashes `/`)
   - Verify file exists in `_static` directory
   - Ensure correct file extension

2. **Image too large/small**
   - Use `:width:` or `:scale:` options
   - Consider responsive sizing with percentages

3. **Poor image quality**
   - Use higher resolution source images
   - Choose appropriate format (PNG for screenshots, SVG for diagrams)

### Path Examples
```markdown
# Correct paths (from doc/source/ perspective)
/_static/images/screenshot.png
/_static/images/diagrams/workflow.svg
/_static/images/logos/logo.png

# Incorrect paths
../images/screenshot.png
/static/images/screenshot.png
images/screenshot.png
```

## Integration with Build Process

When you build the documentation with `make html`, Sphinx will:
1. Copy all files from `_static/` to the output directory
2. Process image references and generate proper HTML
3. Optimize paths for web viewing

The built documentation will have images accessible at:
`doc/build/html/_static/images/your_image.png`
