"""CLI for envschema - .env.example exporter."""

import argparse
import sys
from typing import List, Optional

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


def export_example(
    schemas: List[EnvSchema], output: Optional[str] = None
) -> str:
    """Export .env.example content from schemas.

    Args:
        schemas: List of EnvSchema definitions
        output: Optional file path to write the example to

    Returns:
        The generated .env.example content as a string
    """
    content = build_example(schemas)
    if output:
        with open(output, "w") as f:
            f.write(content)
    return content


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="envschema - Zero-dependency typed .env validator"
    )
    parser.add_argument(
        "--export-example",
        action="store_true",
        help="Generate .env.example from schema definitions",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".env.example",
        help="Output file path (default: .env.example)",
    )
    args = parser.parse_args(argv)

    if args.export_example:
        print("Use export_example() in Python with your EnvSchema list")
        print(f"Example output would be written to: {args.output}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
