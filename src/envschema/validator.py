"""Core validation logic for environment variables."""

import os
from typing import Any, Callable, Dict, Iterable, List, Optional, Type, Union


class ValidationError(Exception):
    """Raised when environment variable validation fails."""
    pass


class EnvSchema:
    """Define schema for environment variable validation."""

    def __init__(
        self,
        name: str,
        var_type: Type = str,
        required: bool = True,
        default: Optional[Any] = None,
        validator: Optional[Callable[[Any], bool]] = None,
        choices: Optional[Iterable[Any]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        secret: bool = False,
    ):
        """Initialize an environment variable schema.

        Args:
            name: Environment variable name
            var_type: Expected type (str, int, float, bool, list)
            required: Whether the variable is required
            default: Default value if not required and not present
            validator: Optional custom validation function
            choices: Allowed values (membership check)
            min_value: Minimum allowed value (int/float only)
            max_value: Maximum allowed value (int/float only)
            secret: Mask value in repr() output
        """
        self.name = name
        self.var_type = var_type
        self.required = required
        self.default = default
        self.validator = validator
        self.choices = set(choices) if choices is not None else None
        self.min_value = min_value
        self.max_value = max_value
        self.secret = secret

    def __repr__(self) -> str:
        masked = "****" if self.secret else repr(self.default)
        return (
            f"EnvSchema(name={self.name!r}, type={self.var_type.__name__}, "
            f"required={self.required}, default={masked})"
        )


class EnvValidator:
    """Validate environment variables against a schema."""

    def __init__(self, schemas: List[EnvSchema]):
        """Initialize validator with schemas."""
        self.schemas = schemas

    def _parse_value(self, value: str, var_type: Type) -> Any:
        """Parse string value to the specified type."""
        if var_type == str:
            return value
        elif var_type == int:
            try:
                return int(value)
            except ValueError:
                raise ValidationError(f"Cannot convert '{value}' to int")
        elif var_type == float:
            try:
                return float(value)
            except ValueError:
                raise ValidationError(f"Cannot convert '{value}' to float")
        elif var_type == bool:
            lower_val = value.lower()
            if lower_val in ("true", "1", "yes", "on"):
                return True
            elif lower_val in ("false", "0", "no", "off"):
                return False
            else:
                raise ValidationError(f"Cannot convert '{value}' to bool")
        elif var_type == list:
            return [item.strip() for item in value.split(",") if item.strip()]
        else:
            raise ValidationError(f"Unsupported type: {var_type}")

    def _check_constraints(self, schema: EnvSchema, parsed: Any) -> None:
        """Run choices/range/custom validators on parsed value."""
        if schema.choices is not None and parsed not in schema.choices:
            raise ValidationError(
                f"Variable '{schema.name}' value {parsed!r} not in choices {sorted(schema.choices)}"
            )
        if schema.min_value is not None:
            if not isinstance(parsed, (int, float)):
                raise ValidationError(
                    f"Variable '{schema.name}' min_value requires numeric type"
                )
            if parsed < schema.min_value:
                raise ValidationError(
                    f"Variable '{schema.name}' value {parsed} below min {schema.min_value}"
                )
        if schema.max_value is not None:
            if not isinstance(parsed, (int, float)):
                raise ValidationError(
                    f"Variable '{schema.name}' max_value requires numeric type"
                )
            if parsed > schema.max_value:
                raise ValidationError(
                    f"Variable '{schema.name}' value {parsed} above max {schema.max_value}"
                )
        if schema.validator and not schema.validator(parsed):
            raise ValidationError(
                f"Variable '{schema.name}' failed custom validation"
            )

    def validate(self, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Validate environment variables against schemas."""
        if env is None:
            env = dict(os.environ)

        result: Dict[str, Any] = {}

        for schema in self.schemas:
            value = env.get(schema.name)

            if value is None:
                if schema.required:
                    raise ValidationError(
                        f"Required variable '{schema.name}' is missing"
                    )
                else:
                    result[schema.name] = schema.default
                    continue

            try:
                parsed_value = self._parse_value(value, schema.var_type)
            except ValidationError as e:
                raise ValidationError(f"Variable '{schema.name}': {e}")

            self._check_constraints(schema, parsed_value)
            result[schema.name] = parsed_value

        return result

    def load_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load and validate environment variables from a .env file."""
        env: Dict[str, str] = {}

        with open(filepath, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    raise ValidationError(
                        f"Invalid line {line_num} in {filepath}: missing '='"
                    )

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                env[key] = value

        return self.validate(env)
