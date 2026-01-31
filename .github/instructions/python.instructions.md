---
description: 'Python 3.14 coding conventions and guidelines with UV package manager'
applyTo: '**/*.py, **/pyproject.toml, **/uv.lock'
---

# Python 3.14 Coding Conventions and UV Workflow

## ⚠️ CRITICAL: Always Use UV for All Python Operations

**IMPORTANT:** GitHub Copilot MUST use `uv` for ALL Python-related operations in this project. Never use `python`, `pip`, `pytest`, or other tools directly without prefixing with `uv run`.

### UV Command Pattern

All Python operations follow this pattern:
```bash
uv run <command>
```

Examples:
```bash
uv run python script.py              # Run Python scripts
uv run pytest                        # Run tests
uv run pytest tests/                 # Run specific test directory
uv run pytest tests/test_file.py     # Run specific test file
uv run mypy src/                     # Type checking
uv run ruff check src/               # Linting
uv run black src/                    # Code formatting
uv run python -m pip list            # List packages
uv sync                              # Install dependencies from lock file
```

**Never use these directly:**
- ❌ `python script.py` → ✅ `uv run python script.py`
- ❌ `pytest` → ✅ `uv run pytest`
- ❌ `pip install` → ✅ `uv add`
- ❌ `mypy` → ✅ `uv run mypy`
- ❌ `black` → ✅ `uv run black`
- ❌ `ruff` → ✅ `uv run ruff`

## Project Setup with UV

**UV is the standard Python package manager** - it's faster, more reliable, and replaces pip, poetry, pipenv, and pyenv.

### Installation

Install UV using the official installer:
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Initialize New Projects

```bash
# Create a new project with Python 3.14
uv init my-project

# This creates:
# - pyproject.toml (project config)
# - .python-version (set to 3.14)
# - .venv/ (managed virtual environment)
# - uv.lock (lockfile for reproducibility)
```

### Dependency Management

```bash
# Add a package (with optional version specifier)
uv add numpy
uv add "pandas>=2.0,<3.0"

# Remove a package
uv remove numpy

# Update dependencies
uv lock --upgrade

# Install from existing lockfile
uv sync
```

### Running Scripts and Commands

```bash
# Run Python scripts with correct environment (Python 3.14)
uv run python script.py
uv run pytest
uv run mypy src/

# No manual venv activation needed - UV handles it automatically
```

### Python Version Management

```bash
# Ensure Python 3.14 is installed
uv python install 3.14

# Pin project to Python 3.14
uv python pin 3.14

# Use multiple interpreters (e.g., test on 3.13 and 3.14)
uv run --python 3.13 pytest
uv run --python 3.14 pytest
```

### Configuration: `pyproject.toml`

All project metadata and dependencies go in `pyproject.toml`:

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome project"
requires-python = ">=3.14"
dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black",
    "mypy",
    "ruff",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0",
    "black",
    "mypy",
    "ruff",
]
```

### Lockfile Management: `uv.lock`

- **Always commit `uv.lock` to version control** for reproducible builds
- Lockfile ensures exact dependency versions across all environments (dev, CI/CD, production)
- Automatically updated when running `uv add`, `uv remove`, or `uv lock`
- Never manually edit - let UV manage it

### CI/CD and Docker Integration

```dockerfile
FROM python:3.14-slim

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "python", "main.py"]
```

```yaml
# GitHub Actions
- name: Install UV
  uses: astral-sh/setup-uv@v2

- name: Set Python 3.14
  uses: actions/setup-python@v5
  with:
    python-version: '3.14'

- name: Install dependencies
  run: uv sync --frozen

- name: Run tests
  run: uv run pytest
```

### Migration from Legacy Tools

**From pip + requirements.txt:**
```bash
# Convert requirements.txt to pyproject.toml
uv init --requirements requirements.txt
```

**From poetry:**
```bash
# UV can use poetry.lock initially
uv sync
# Then migrate gradually to pyproject.toml
```

---

## Python 3.14 Features & Best Practices

### ✨ Deferred Evaluation of Annotations (PEP 649)

Type annotations are now deferred by default, improving performance and reducing overhead:

```python
from typing import List
from annotationlib import get_annotations

def process_data(items: List[str]) -> dict[str, int]:
    """Process items and return count.
    
    With deferred annotations, type hints don't slow down function definition.
    Use annotationlib for runtime introspection when needed.
    """
    return {item: len(item) for item in items}

# Get annotations only when needed
if __name__ == "__main__":
    annotations = get_annotations(process_data)
    print(annotations)
```

### 🧵 Free-Threaded Python (PEP 779)

Leverage true parallelism without the GIL for multi-core workloads:

```python
import threading
from concurrent.interpreters import InterpreterPoolExecutor

def cpu_bound_task(n: int) -> int:
    """CPU-intensive task that benefits from free threading."""
    return sum(i ** 2 for i in range(n))

# With free-threaded Python, this runs truly parallel
with InterpreterPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(cpu_bound_task, [1000000] * 4))
    print(f"Results: {results}")
```

### 🔀 Multiple Interpreters (PEP 734)

Run isolated Python interpreters in the same process:

```python
from concurrent.interpreters import create_interpreter, run_string

def run_isolated_code():
    """Create and run code in an isolated interpreter."""
    interp = create_interpreter()
    code = """
import sys
result = sum(range(1000000))
print(f"Isolated calculation: {result}")
"""
    run_string(interp, code)

run_isolated_code()
```

### 🎯 Template String Literals (PEP 750)

Use t-strings for safer, controlled string interpolation:

```python
from typing import Any

def format_with_template(name: str, value: Any) -> str:
    """T-strings provide safer interpolation than f-strings.
    
    Useful for SQL, templates, and security-sensitive contexts.
    """
    # t-strings defer evaluation for safer handling
    query = t"SELECT * FROM users WHERE name = {name}"
    return query
```

### 🎨 Enhanced Developer Experience

Colored output and syntax highlighting in REPL and errors:

```python
# Python 3.14 REPL now supports syntax highlighting and color
# Try running:
# python3.14 -i script.py

# Better error messages with colors and suggestions
def calculate(x: int) -> str:
    """Better error messages guide you to fixes."""
    return x + "string"  # TypeError now shows in color with suggestion

# Exception tracing includes color-coded stack traces
```

---

## Python Coding Conventions

### Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use deferred annotations with Python 3.14 (automatic by default).
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`).
- Break down complex functions into smaller, more manageable functions.

### General Guidelines

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.
- Leverage modern Python 3.14 features (free threading, deferred annotations).

### Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 79 characters (or 88 for black).
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.
- Use tools to enforce style:
  - **`black`**: Code formatting (add via `uv add --group dev black`)
  - **`ruff`**: Linting and import sorting (add via `uv add --group dev ruff`)
  - **`mypy`**: Static type checking (add via `uv add --group dev mypy`)

### Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.
- Run tests with: `uv run pytest`

### Example of Proper Documentation (Python 3.14)

```python
from typing import Any

def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    
    This function uses deferred type annotations for better performance.
    Type hints are evaluated only when introspected via annotationlib.
    
    Args:
        radius: The radius of the circle in units.
    
    Returns:
        The area of the circle, calculated as π * radius².
    
    Raises:
        ValueError: If radius is negative.
    
    Example:
        >>> calculate_area(5.0)
        78.53981633974483
    """
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    import math
    return math.pi * radius ** 2


# Using t-strings for template safety
def build_safe_query(table: str, condition: str) -> str:
    """Build a database query safely using template strings.
    
    T-strings provide controlled interpolation without f-string overhead.
    """
    query = t"SELECT * FROM {table} WHERE {condition}"
    return query


# Leverage free threading for parallel tasks
from concurrent.interpreters import InterpreterPoolExecutor

def parallel_computation(data: list[int]) -> list[int]:
    """Compute results in parallel using free-threaded Python 3.14.
    
    With the GIL removed, true multi-core parallelism is possible.
    """
    with InterpreterPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda x: x ** 2, data))
    return results
```

---

## Python 3.14 Specific Features to Use

✨ **New in 3.14:**
- 🚀 Free threading without GIL for CPU-bound workloads
- 📋 Deferred annotations for better performance
- 🔀 Multiple interpreters in one process
- 🎯 T-strings for safe template interpolation
- 🎨 Colored error messages and REPL
- ⚡ Experimental JIT compiler for performance (opt-in)

---

## Best Practices Summary

✅ **DO:**
- Use `uv` for all Python package management
- Commit both `pyproject.toml` and `uv.lock`
- Pin Python version to 3.14 in `.python-version` file
- Use `uv run` for executing scripts and tests
- Use type hints extensively (leverage deferred annotations)
- Follow PEP 8 and use formatters (black, ruff)
- Use free threading for CPU-bound parallel tasks
- Require Python 3.14+ for new projects

❌ **DON'T:**
- Manually edit `uv.lock` or `pyproject.toml` dependencies
- Use `pip` directly when UV is available
- Skip virtual environment isolation
- Create Python scripts without type hints
- Commit code that hasn't been formatted with `black` and checked with `ruff`
- Use Python < 3.14 for new projects (unless legacy support required)
- Disable free threading without good reason