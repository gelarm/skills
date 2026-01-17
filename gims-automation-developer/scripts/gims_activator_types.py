#!/usr/bin/env python3
"""CLI for GIMS Activator Types management."""

import argparse
import sys
from gims_client import GimsClient, GimsApiError, print_error, print_json


def build_folder_paths(folders: list[dict]) -> dict[int, str]:
    """Build folder ID to path mapping.
    
    Root folders get path "/" + name (e.g., "/default").
    Nested folders get full path (e.g., "/default/SNMP_Rules_v1.2").
    """
    folder_map = {f["id"]: f for f in folders}
    paths = {}

    def get_path(folder_id: int) -> str:
        if folder_id in paths:
            return paths[folder_id]
        folder = folder_map.get(folder_id)
        if not folder:
            return ""
        parent_id = folder.get("parent_folder_id")
        if parent_id:
            parent_path = get_path(parent_id)
            paths[folder_id] = f"{parent_path}/{folder['name']}"
        else:
            # Root folder: path starts with "/"
            paths[folder_id] = f"/{folder['name']}"
        return paths[folder_id]

    for folder in folders:
        get_path(folder["id"])

    return paths


# Folder commands

def cmd_list_folders(args):
    """List all activator type folders."""
    client = GimsClient()
    folders = client.request("GET", "/activator-types/folder/")
    paths = build_folder_paths(folders)

    result = []
    for folder in folders:
        result.append({
            "id": folder["id"],
            "name": folder["name"],
            "path": paths.get(folder["id"], folder["name"]),
            "parent_folder_id": folder.get("parent_folder_id"),
        })

    print_json({"folders": result})


def cmd_create_folder(args):
    """Create an activator type folder."""
    client = GimsClient()
    data = {"name": args.name}
    if args.parent_folder_id:
        data["parent_folder_id"] = args.parent_folder_id
    result = client.request("POST", "/activator-types/folder/", json=data)
    print_json(result)


def cmd_update_folder(args):
    """Update an activator type folder."""
    client = GimsClient()
    data = {}
    if args.name:
        data["name"] = args.name
    if args.parent_folder_id is not None:
        data["parent_folder_id"] = args.parent_folder_id if args.parent_folder_id > 0 else None

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/activator-types/folder/{args.folder_id}/", json=data)
    print_json(result)


def cmd_delete_folder(args):
    """Delete an activator type folder."""
    client = GimsClient()
    client.request("DELETE", f"/activator-types/folder/{args.folder_id}/")
    print(f"Folder {args.folder_id} deleted successfully")


# Type commands

def cmd_list(args):
    """List all activator types."""
    client = GimsClient()
    folders = client.request("GET", "/activator-types/folder/")
    paths = build_folder_paths(folders)

    types = client.request("GET", "/activator-types/activator-type/")

    if args.folder_id:
        types = [t for t in types if t.get("folder") == args.folder_id]

    result = []
    for t in types:
        folder_id = t.get("folder")
        result.append({
            "id": t["id"],
            "name": t["name"],
            "description": t.get("description", ""),
            "version": t.get("version", ""),
            "folder_path": paths.get(folder_id, "/") if folder_id else "/",
            "folder_id": folder_id,
        })

    print_json({"types": result})


def cmd_get(args):
    """Get an activator type by ID."""
    client = GimsClient()
    act_type = client.request("GET", f"/activator-types/activator-type/{args.type_id}/")

    # Filter code unless explicitly requested
    if not args.include_code:
        act_type["code"] = "[FILTERED] Use --include-code or get-code command"

    result = {"type": act_type}

    if args.include_properties:
        properties = client.request("GET", f"/activator-types/property/?activator_type_id={args.type_id}")
        result["properties"] = properties

    print_json(result)


def cmd_get_code(args):
    """Get only activator type code."""
    client = GimsClient()
    act_type = client.request("GET", f"/activator-types/activator-type/{args.type_id}/")
    print(act_type.get("code", ""))


def cmd_create(args):
    """Create an activator type."""
    client = GimsClient()
    data = {"name": args.name}

    if args.code:
        data["code"] = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            data["code"] = f.read()
    else:
        data["code"] = "# Print all built-in variables and functions for help\nprint_help()"

    if args.description:
        data["description"] = args.description
    if args.version:
        data["version"] = args.version
    else:
        data["version"] = "1.0"
    if args.folder_id:
        data["folder"] = args.folder_id

    result = client.request("POST", "/activator-types/activator-type/", json=data)
    print_json(result)


def cmd_update(args):
    """Update an activator type."""
    client = GimsClient()
    data = {}

    if args.name:
        data["name"] = args.name
    if args.description:
        data["description"] = args.description
    if args.version:
        data["version"] = args.version
    if args.code:
        data["code"] = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            data["code"] = f.read()
    if args.folder_id is not None:
        data["folder"] = args.folder_id if args.folder_id > 0 else None

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/activator-types/activator-type/{args.type_id}/", json=data)
    print_json(result)


def cmd_delete(args):
    """Delete an activator type."""
    client = GimsClient()
    client.request("DELETE", f"/activator-types/activator-type/{args.type_id}/")
    print(f"Activator type {args.type_id} deleted successfully")


def cmd_search(args):
    """Search activator types."""
    import re
    client = GimsClient()
    types = client.request("GET", "/activator-types/activator-type/")

    query = args.query
    flags = 0 if args.case_sensitive else re.IGNORECASE

    results = []
    found_ids = set()

    # Search by name
    if args.search_in in ("name", "both"):
        for t in types:
            name = t.get("name", "")
            if re.search(query, name, flags):
                results.append({
                    "id": t["id"],
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "matched_in": "name",
                })
                found_ids.add(t["id"])

    # Search by code
    if args.search_in in ("code", "both"):
        for t in types:
            if t["id"] in found_ids:
                continue
            full_type = client.request("GET", f"/activator-types/activator-type/{t['id']}/")
            code = full_type.get("code", "")
            if re.search(query, code, flags):
                results.append({
                    "id": t["id"],
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "matched_in": "code",
                })

    print_json({"results": results, "count": len(results)})


# Property commands

def cmd_list_properties(args):
    """List properties of an activator type."""
    client = GimsClient()
    properties = client.request("GET", f"/activator-types/property/?activator_type_id={args.type_id}")
    print_json({"properties": properties})


def cmd_create_property(args):
    """Create a property for an activator type."""
    client = GimsClient()
    data = {
        "activator_type_id": args.type_id,
        "name": args.name,
        "label": args.label,
        "value_type_id": args.value_type_id,
        "section_name_id": args.section_id,
    }

    if args.description:
        data["description"] = args.description
    if args.default_value:
        data["default_value"] = args.default_value
    if args.is_required:
        data["is_required"] = True
    if args.is_hidden:
        data["is_hidden"] = True
    if args.default_dict_value_id:
        data["default_dict_value_id"] = args.default_dict_value_id

    result = client.request("POST", "/activator-types/property/", json=data)
    print_json(result)


def cmd_update_property(args):
    """Update an activator type property."""
    client = GimsClient()
    data = {}

    if args.name:
        data["name"] = args.name
    if args.label:
        data["label"] = args.label
    if args.description is not None:
        data["description"] = args.description
    if args.default_value is not None:
        data["default_value"] = args.default_value
    if args.is_required is not None:
        data["is_required"] = args.is_required
    if args.is_hidden is not None:
        data["is_hidden"] = args.is_hidden

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/activator-types/property/{args.property_id}/", json=data)
    print_json(result)


def cmd_delete_property(args):
    """Delete an activator type property."""
    client = GimsClient()
    client.request("DELETE", f"/activator-types/property/{args.property_id}/")
    print(f"Property {args.property_id} deleted successfully")


def main():
    parser = argparse.ArgumentParser(
        description="GIMS Activator Types CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Folders
    subparsers.add_parser("list-folders", help="List all activator type folders")

    create_folder = subparsers.add_parser("create-folder", help="Create a folder")
    create_folder.add_argument("--name", required=True, help="Folder name")
    create_folder.add_argument("--parent-folder-id", type=int, help="Parent folder ID")

    update_folder = subparsers.add_parser("update-folder", help="Update a folder")
    update_folder.add_argument("folder_id", type=int, help="Folder ID")
    update_folder.add_argument("--name", help="New name")
    update_folder.add_argument("--parent-folder-id", type=int, help="New parent folder ID")

    delete_folder = subparsers.add_parser("delete-folder", help="Delete a folder")
    delete_folder.add_argument("folder_id", type=int, help="Folder ID")

    # Types
    list_cmd = subparsers.add_parser("list", help="List all activator types")
    list_cmd.add_argument("--folder-id", type=int, help="Filter by folder ID")

    get_cmd = subparsers.add_parser("get", help="Get an activator type")
    get_cmd.add_argument("type_id", type=int, help="Type ID")
    get_cmd.add_argument("--include-code", action="store_true", help="Include code in output")
    get_cmd.add_argument("--no-properties", dest="include_properties", action="store_false",
                         help="Exclude properties")
    get_cmd.set_defaults(include_properties=True)

    get_code = subparsers.add_parser("get-code", help="Get only activator type code")
    get_code.add_argument("type_id", type=int, help="Type ID")

    create_cmd = subparsers.add_parser("create", help="Create an activator type")
    create_cmd.add_argument("--name", required=True, help="Type name")
    create_cmd.add_argument("--code", help="Python code")
    create_cmd.add_argument("--code-file", help="Read code from file")
    create_cmd.add_argument("--description", help="Description")
    create_cmd.add_argument("--version", help="Version (default: 1.0)")
    create_cmd.add_argument("--folder-id", type=int, help="Folder ID")

    update_cmd = subparsers.add_parser("update", help="Update an activator type")
    update_cmd.add_argument("type_id", type=int, help="Type ID")
    update_cmd.add_argument("--name", help="New name")
    update_cmd.add_argument("--code", help="New code")
    update_cmd.add_argument("--code-file", help="Read code from file")
    update_cmd.add_argument("--description", help="New description")
    update_cmd.add_argument("--version", help="New version")
    update_cmd.add_argument("--folder-id", type=int, help="New folder ID (0 to remove)")

    delete_cmd = subparsers.add_parser("delete", help="Delete an activator type")
    delete_cmd.add_argument("type_id", type=int, help="Type ID")

    search_cmd = subparsers.add_parser("search", help="Search activator types")
    search_cmd.add_argument("--query", required=True, help="Search query (regex)")
    search_cmd.add_argument("--search-in", choices=["name", "code", "both"], default="name",
                            help="Where to search (default: name)")
    search_cmd.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")

    # Properties
    list_props = subparsers.add_parser("list-properties", help="List properties of an activator type")
    list_props.add_argument("type_id", type=int, help="Activator type ID")

    create_prop = subparsers.add_parser("create-property", help="Create a property")
    create_prop.add_argument("--type-id", type=int, required=True, help="Activator type ID")
    create_prop.add_argument("--name", required=True, help="Property display name")
    create_prop.add_argument("--label", required=True, help="Property label (variable name in code)")
    create_prop.add_argument("--value-type-id", type=int, required=True, help="Value type ID")
    create_prop.add_argument("--section-id", type=int, required=True, help="Section ID")
    create_prop.add_argument("--description", help="Description")
    create_prop.add_argument("--default-value", help="Default value")
    create_prop.add_argument("--is-required", action="store_true", help="Is required")
    create_prop.add_argument("--is-hidden", action="store_true", help="Is hidden")
    create_prop.add_argument("--default-dict-value-id", type=int, help="Default dictionary value ID")

    update_prop = subparsers.add_parser("update-property", help="Update a property")
    update_prop.add_argument("property_id", type=int, help="Property ID")
    update_prop.add_argument("--name", help="New name")
    update_prop.add_argument("--label", help="New label")
    update_prop.add_argument("--description", help="New description")
    update_prop.add_argument("--default-value", help="New default value")
    update_prop.add_argument("--is-required", type=lambda x: x.lower() == 'true', help="Is required (true/false)")
    update_prop.add_argument("--is-hidden", type=lambda x: x.lower() == 'true', help="Is hidden (true/false)")

    delete_prop = subparsers.add_parser("delete-property", help="Delete a property")
    delete_prop.add_argument("property_id", type=int, help="Property ID")

    args = parser.parse_args()

    try:
        handlers = {
            "list-folders": cmd_list_folders,
            "create-folder": cmd_create_folder,
            "update-folder": cmd_update_folder,
            "delete-folder": cmd_delete_folder,
            "list": cmd_list,
            "get": cmd_get,
            "get-code": cmd_get_code,
            "create": cmd_create,
            "update": cmd_update,
            "delete": cmd_delete,
            "search": cmd_search,
            "list-properties": cmd_list_properties,
            "create-property": cmd_create_property,
            "update-property": cmd_update_property,
            "delete-property": cmd_delete_property,
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
