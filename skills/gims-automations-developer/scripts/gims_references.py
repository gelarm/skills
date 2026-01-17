#!/usr/bin/env python3
"""CLI for GIMS Reference data (ValueTypes, PropertySections)."""

import argparse
import sys
from gims_client import GimsClient, GimsApiError, print_error, print_json


def cmd_list_value_types(args):
    """List all available value types for properties and parameters."""
    client = GimsClient()
    types = client.request("GET", "/value-types/value-type/")
    print_json({"value_types": types})


def cmd_list_property_sections(args):
    """List all available property sections."""
    client = GimsClient()
    sections = client.request("GET", "/property-sections/section-name/")
    print_json({"property_sections": sections})


def main():
    parser = argparse.ArgumentParser(
        description="GIMS Reference Data CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s value-types     List all value types (for properties/parameters)
  %(prog)s sections        List all property sections
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("value-types", help="List all value types")
    subparsers.add_parser("sections", help="List all property sections")

    args = parser.parse_args()

    try:
        handlers = {
            "value-types": cmd_list_value_types,
            "sections": cmd_list_property_sections,
        }
        handlers[args.command](args)
    except GimsApiError as e:
        print_error(f"{e.message}\nDetail: {e.detail}")
        sys.exit(1)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
