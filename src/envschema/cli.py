"""CLI for envschema - .env.example exporter."""

import argparse
import sys
from typing import List

from .validator import EnvSchema


def build_example(schemas: List[EnvSchema]) -> str:
    """Build a .env.example content from schemas."""
    lines: List[str] = ["# Environment variables", ""]
    for schema in schemas:
        if schema.secret:
            example = "your-secret-here"
        elif schema.default is not None:
            example = str(schema.default)
        elif schema.var_type == int:
            example = "0"
        elif schema.var_type == float:
            example = "0.0"
        elif schema.var_type == bool:
            example = "true"
        elif schema.var_type == list:
            example = "item1,item2"
        else:
            example = "your-value-here"
        lines.append(f"{schema.name}={example}")
    lines.append("")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="envschema - Export .env.example from schema definitions"
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".env.example",
        help="Output file path (default: .env.example)",
    )
    args = parser.parse_args(argv)

    # Import here to avoid circular import when used as library only
    from . import EnvSchema as _  # noqa: F401

    print("envschema CLI: define schemas in Python and call build_example()")
    print(f"Example output would be written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
