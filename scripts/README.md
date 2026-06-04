# Scripts

Utility scripts for data processing, debugging, and testing.

## Running Scripts

Scripts in this directory import modules from the project's `core/` package.

Because of this, scripts should be run as Python modules from the project root:

```bash
python -m scripts.clean_products
python -m scripts.test_full_text
python -m scripts.inspect_headers
```

Do NOT run scripts directly:

```bash
python scripts/clean_products.py      # ❌ May cause import errors
python scripts/test_full_text.py      # ❌ May cause import errors
```

Running with `-m` ensures that the project root is added to Python's import path and allows imports such as:

```python
from core.schema import ...
from core.utils import ...
```

to work correctly.

## Adding New Scripts

1. Create a new file in `scripts/`.
2. Run it using:

```bash
python -m scripts.<script_name>
```

Example:

```bash
python -m scripts.normalize_products
```