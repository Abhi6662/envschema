# envschema

Zero-dependency typed `.env` validator and loader for Python.

## Features

- Type-safe parsing: `str`, `int`, `float`, `bool`, `list`
- Required/optional variables with defaults
- `choices`, `min_value`, `max_value` constraints
- Custom validator callables
- `.env` file loading with quote stripping
- Secret masking in `repr()`
- `.env.example` exporter via CLI

## Installation

```bash
pip install envschema
```

## Usage

```python
from envschema import EnvSchema, EnvValidator

schemas = [
    EnvSchema("APP_NAME", var_type=str, required=True),
    EnvSchema("PORT", var_type=int, required=True, min_value=1024, max_value=65535),
    EnvSchema("DEBUG", var_type=bool, required=False, default=False),
    EnvSchema("API_KEY", var_type=str, required=True, secret=True),
    EnvSchema("ALLOWED_HOSTS", var_type=list, required=False, default=[]),
]

validator = EnvValidator(schemas)
config = validator.validate()
```

## CLI

```bash
envschema --export-example --output .env.example
```

## License

MIT
