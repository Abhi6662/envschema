"""Tests for envschema validator and CLI."""

import os
import tempfile

import pytest

from envschema import EnvSchema, EnvValidator, ValidationError


# --- Basic validation ---


def test_str_required_variable():
    schema = [EnvSchema(name="APP_NAME", var_type=str, required=True)]
    validator = EnvValidator(schema)
    result = validator.validate({"APP_NAME": "myapp"})
    assert result == {"APP_NAME": "myapp"}


def test_str_missing_required_raises():
    schema = [EnvSchema(name="APP_NAME", var_type=str, required=True)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="Required variable"):
        validator.validate({})


def test_optional_with_default():
    schema = [EnvSchema(name="APP_NAME", var_type=str, required=False, default="default-app")]
    validator = EnvValidator(schema)
    result = validator.validate({})
    assert result == {"APP_NAME": "default-app"}


# --- Type parsing ---


def test_int_parsing():
    schema = [EnvSchema(name="PORT", var_type=int, required=True)]
    validator = EnvValidator(schema)
    result = validator.validate({"PORT": "8080"})
    assert result == {"PORT": 8080}
    assert isinstance(result["PORT"], int)


def test_int_invalid_raises():
    schema = [EnvSchema(name="PORT", var_type=int, required=True)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="Cannot convert"):
        validator.validate({"PORT": "not-a-number"})


def test_float_parsing():
    schema = [EnvSchema(name="TIMEOUT", var_type=float, required=True)]
    validator = EnvValidator(schema)
    result = validator.validate({"TIMEOUT": "3.5"})
    assert result == {"TIMEOUT": 3.5}
    assert isinstance(result["TIMEOUT"], float)


def test_bool_parsing_true():
    schema = [EnvSchema(name="DEBUG", var_type=bool, required=True)]
    validator = EnvValidator(schema)
    for val in ("true", "1", "yes", "on"):
        result = validator.validate({"DEBUG": val})
        assert result["DEBUG"] is True


def test_bool_parsing_false():
    schema = [EnvSchema(name="DEBUG", var_type=bool, required=True)]
    validator = EnvValidator(schema)
    for val in ("false", "0", "no", "off"):
        result = validator.validate({"DEBUG": val})
        assert result["DEBUG"] is False


def test_bool_invalid_raises():
    schema = [EnvSchema(name="DEBUG", var_type=bool, required=True)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError):
        validator.validate({"DEBUG": "maybe"})


def test_list_parsing():
    schema = [EnvSchema(name="ALLOWED_HOSTS", var_type=list, required=True)]
    validator = EnvValidator(schema)
    result = validator.validate({"ALLOWED_HOSTS": "a,b,c"})
    assert result == {"ALLOWED_HOSTS": ["a", "b", "c"]}


# --- Constraints ---


def test_choices_allowed():
    schema = [EnvSchema(name="ENV", var_type=str, required=True, choices={"dev", "staging", "prod"})]
    validator = EnvValidator(schema)
    result = validator.validate({"ENV": "prod"})
    assert result == {"ENV": "prod"}


def test_choices_disallowed_raises():
    schema = [EnvSchema(name="ENV", var_type=str, required=True, choices={"dev", "staging", "prod"})]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="not in choices"):
        validator.validate({"ENV": "invalid"})


def test_min_value_ok():
    schema = [EnvSchema(name="PORT", var_type=int, required=True, min_value=1024)]
    validator = EnvValidator(schema)
    result = validator.validate({"PORT": "8080"})
    assert result == {"PORT": 8080}


def test_min_value_violated_raises():
    schema = [EnvSchema(name="PORT", var_type=int, required=True, min_value=1024)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="below min"):
        validator.validate({"PORT": "80"})


def test_max_value_violated_raises():
    schema = [EnvSchema(name="PORT", var_type=int, required=True, max_value=65535)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="above max"):
        validator.validate({"PORT": "99999"})


def test_custom_validator():
    def is_positive(value):
        return value > 0

    schema = [EnvSchema(name="COUNT", var_type=int, required=True, validator=is_positive)]
    validator = EnvValidator(schema)
    with pytest.raises(ValidationError, match="custom validation"):
        validator.validate({"COUNT": "-1"})


# --- .env file loading ---


def test_load_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_NAME=myapp\nPORT=8080\nDEBUG=true\n")
        path = f.name
    try:
        schemas = [
            EnvSchema(name="APP_NAME", var_type=str, required=True),
            EnvSchema(name="PORT", var_type=int, required=True),
            EnvSchema(name="DEBUG", var_type=bool, required=True),
        ]
        validator = EnvValidator(schemas)
        result = validator.load_from_file(path)
        assert result == {"APP_NAME": "myapp", "PORT": 8080, "DEBUG": True}
    finally:
        os.unlink(path)


def test_load_from_file_invalid_line():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_NAME=myapp\nbadline\n")
        path = f.name
    try:
        schemas = [EnvSchema(name="APP_NAME", var_type=str, required=True)]
        validator = EnvValidator(schemas)
        with pytest.raises(ValidationError, match="missing '='"):
            validator.load_from_file(path)
    finally:
        os.unlink(path)


# --- Secret masking ---


def test_secret_masked_in_repr():
    schema = EnvSchema(name="API_KEY", var_type=str, required=True, secret=True, default="sk-12345")
    r = repr(schema)
    assert "****" in r
    assert "sk-12345" not in r


def test_non_secret_not_masked():
    schema = EnvSchema(name="APP_NAME", var_type=str, required=True, default="myapp")
    r = repr(schema)
    assert "myapp" in r
    assert "****" not in r
