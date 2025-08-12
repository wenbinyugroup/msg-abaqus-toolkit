# Markdown Support in Sphinx Documentation

This project now supports writing documentation in Markdown format using MyST-Parser.

## What's Been Set Up

### 1. Dependencies Added
- `myst-parser>=0.18.0` - The core markdown parser for Sphinx
- `sphinx>=4.0` - Sphinx documentation generator
- `sphinx-immaterial` - Material theme for Sphinx

### 2. Sphinx Configuration Updated
The `doc/source/conf.py` file has been updated with:
- MyST-Parser extension enabled
- Support for both `.rst` and `.md` files
- Enhanced MyST features enabled (math, admonitions, code blocks, etc.)

### 3. Sample Files Created
- `getting_started.md` - Introduction and quick start guide
- `user_guide.md` - Comprehensive user documentation
- `api_reference.md` - API documentation with code examples

## How to Use Markdown in Your Documentation

### Basic Markdown Syntax
All standard Markdown syntax is supported:
- Headers (`#`, `##`, `###`)
- Lists (ordered and unordered)
- Links and images
- Code blocks and inline code
- Tables

### MyST Extensions
MyST-Parser adds powerful extensions to standard Markdown:

#### Admonitions
```markdown
```{note}
This is a note admonition.
```

```{warning}
This is a warning admonition.
```

```{tip}
This is a tip admonition.
```
```

#### Math Support
- Inline math: `$E = mc^2$`
- Block math:
  ```markdown
  $$
  \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
  $$
  ```

#### Code Blocks with Captions
```markdown
```{code-block} python
:caption: Example Python code

def hello_world():
    print("Hello, World!")
```
```

#### Cross-References
```markdown
See [Getting Started](getting_started.md) for more information.
```

#### Table of Contents
```markdown
```{contents}
:local:
:depth: 2
```
```

#### Including reStructuredText
You can still use reStructuredText directives in Markdown:
```markdown
```{eval-rst}
.. automodule:: mymodule
   :members:
```
```

## Building the Documentation

### Install Dependencies
```bash
# Install the project with documentation dependencies
pip install -e .
```

### Build HTML Documentation
```bash
cd doc
make html
```

### View Documentation
Open `doc/build/html/index.html` in your browser.

## File Organization

- Place all documentation source files in `doc/source/`
- Use either `.md` or `.rst` extensions
- Update `doc/source/index.rst` to include new files in the toctree
- Static files (images, CSS) go in `doc/source/_static/`

## Best Practices

1. **Use descriptive filenames** - `user_guide.md` instead of `guide.md`
2. **Organize by topic** - Group related content in subdirectories
3. **Include cross-references** - Link between related sections
4. **Use admonitions** - Highlight important information
5. **Test builds regularly** - Ensure all links and references work

## Troubleshooting

### Common Issues
- **Missing dependencies**: Run `pip install -e .` to install all dependencies
- **Build errors**: Check for syntax errors in Markdown files
- **Missing files**: Ensure all referenced files exist and are included in toctree

### Getting Help
- [MyST-Parser Documentation](https://myst-parser.readthedocs.io/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Markdown Guide](https://www.markdownguide.org/)
