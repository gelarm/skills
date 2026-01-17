#!/usr/bin/env python3
"""CLI for GIMS DataSource Types management."""

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


# ==================== Folders ====================

def cmd_list_folders(args):
    """List all datasource type folders."""
    client = GimsClient()
    folders = client.request("GET", "/datasource_types/folder/")
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
    """Create a folder."""
    client = GimsClient()
    data = {"name": args.name}
    if args.parent_folder_id:
        data["parent_folder_id"] = args.parent_folder_id
    result = client.request("POST", "/datasource_types/folder/", json=data)
    print_json(result)


def cmd_delete_folder(args):
    """Delete a folder."""
    client = GimsClient()
    client.request("DELETE", f"/datasource_types/folder/{args.folder_id}/")
    print(f"Folder {args.folder_id} deleted successfully")


# ==================== Types ====================

def cmd_list(args):
    """List all datasource types."""
    client = GimsClient()
    folders = client.request("GET", "/datasource_types/folder/")
    paths = build_folder_paths(folders)

    types = client.request("GET", "/datasource_types/ds_type/")

    result = []
    for ds_type in types:
        folder_id = ds_type.get("folder")
        result.append({
            "id": ds_type["id"],
            "name": ds_type["name"],
            "description": ds_type.get("description", ""),
            "version": ds_type.get("version", ""),
            "folder_path": paths.get(folder_id, "/") if folder_id else "/",
            "folder_id": folder_id,
        })

    print_json({"types": result})


def cmd_get(args):
    """Get a datasource type with properties and methods."""
    client = GimsClient()
    ds_type = client.request("GET", f"/datasource_types/ds_type/{args.type_id}/")
    result = {"type": ds_type}

    if args.include_properties:
        properties = client.request("GET", "/datasource_types/properties/", params={"mds_type_id": args.type_id})
        result["properties"] = properties

    if args.include_methods:
        methods = client.request("GET", "/datasource_types/method/", params={"mds_type_id": args.type_id})
        # Filter code from methods
        methods_filtered = []
        for method in methods:
            method_filtered = {k: ("[FILTERED]" if k == "code" else v) for k, v in method.items()}
            # Get parameters
            params = client.request("GET", "/datasource_types/method_params/", params={"method_id": method["id"]})
            method_filtered["parameters"] = params
            methods_filtered.append(method_filtered)
        result["methods"] = methods_filtered

    print_json(result)


def cmd_create(args):
    """Create a datasource type."""
    client = GimsClient()
    data = {
        "name": args.name,
        "description": args.description or "",
        "version": args.version or "1.0",
    }
    if args.folder_id:
        data["folder"] = args.folder_id
    result = client.request("POST", "/datasource_types/ds_type/", json=data)
    print_json(result)


def cmd_update(args):
    """Update a datasource type."""
    client = GimsClient()
    data = {}
    if args.name:
        data["name"] = args.name
    if args.description is not None:
        data["description"] = args.description
    if args.version:
        data["version"] = args.version
    if args.folder_id is not None:
        data["folder"] = args.folder_id if args.folder_id > 0 else None

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/datasource_types/ds_type/{args.type_id}/", json=data)
    print_json(result)


def cmd_delete(args):
    """Delete a datasource type."""
    client = GimsClient()
    client.request("DELETE", f"/datasource_types/ds_type/{args.type_id}/")
    print(f"DataSource type {args.type_id} deleted successfully")


# ==================== Properties ====================

def cmd_list_properties(args):
    """List properties of a datasource type."""
    client = GimsClient()
    properties = client.request("GET", "/datasource_types/properties/", params={"mds_type_id": args.type_id})
    print_json({"properties": properties})


def cmd_create_property(args):
    """Create a property."""
    client = GimsClient()
    data = {
        "mds_type_id": args.type_id,
        "name": args.name,
        "label": args.label,
        "value_type_id": args.value_type_id,
        "section_name_id": args.section_id,
        "description": args.description or "",
        "default_value": args.default_value or "",
        "is_required": args.required,
        "is_hidden": args.hidden,
    }
    result = client.request("POST", "/datasource_types/properties/", json=data)
    print_json(result)


def cmd_update_property(args):
    """Update a property."""
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
    if args.required is not None:
        data["is_required"] = args.required
    if args.hidden is not None:
        data["is_hidden"] = args.hidden

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/datasource_types/properties/{args.property_id}/", json=data)
    print_json(result)


def cmd_delete_property(args):
    """Delete a property."""
    client = GimsClient()
    client.request("DELETE", f"/datasource_types/properties/{args.property_id}/")
    print(f"Property {args.property_id} deleted successfully")


# ==================== Methods ====================

def cmd_list_methods(args):
    """List methods of a datasource type (without code)."""
    client = GimsClient()
    methods = client.request("GET", "/datasource_types/method/", params={"mds_type_id": args.type_id})
    # Remove code
    methods_no_code = [{k: v for k, v in m.items() if k != "code"} for m in methods]
    print_json({"methods": methods_no_code})


def cmd_get_method(args):
    """Get method metadata and parameters (code filtered)."""
    client = GimsClient()
    method = client.request("GET", f"/datasource_types/method/{args.method_id}/")
    params = client.request("GET", "/datasource_types/method_params/", params={"method_id": args.method_id})

    method_filtered = {k: ("[FILTERED]" if k == "code" else v) for k, v in method.items()}
    print_json({"method": method_filtered, "parameters": params})


def cmd_get_method_code(args):
    """Get method code."""
    client = GimsClient()
    method = client.request("GET", f"/datasource_types/method/{args.method_id}/")
    print(method.get("code", ""))


def cmd_create_method(args):
    """Create a method."""
    client = GimsClient()

    code = "# Method code\npass"
    if args.code:
        code = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            code = f.read()

    data = {
        "mds_type_id": args.type_id,
        "name": args.name,
        "label": args.label,
        "code": code,
        "description": args.description or "",
    }
    result = client.request("POST", "/datasource_types/method/", json=data)
    print_json(result)


def cmd_update_method(args):
    """Update a method."""
    client = GimsClient()
    data = {}

    if args.name:
        data["name"] = args.name
    if args.label:
        data["label"] = args.label
    if args.description is not None:
        data["description"] = args.description

    if args.code:
        data["code"] = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            data["code"] = f.read()

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/datasource_types/method/{args.method_id}/", json=data)
    print_json(result)


def cmd_delete_method(args):
    """Delete a method."""
    client = GimsClient()
    client.request("DELETE", f"/datasource_types/method/{args.method_id}/")
    print(f"Method {args.method_id} deleted successfully")


# ==================== Method Parameters ====================

def cmd_list_params(args):
    """List method parameters."""
    client = GimsClient()
    params = client.request("GET", "/datasource_types/method_params/", params={"method_id": args.method_id})
    print_json({"parameters": params})


def cmd_create_param(args):
    """Create a method parameter."""
    client = GimsClient()
    data = {
        "method_id": args.method_id,
        "label": args.label,
        "value_type_id": args.value_type_id,
        "input_type": args.input,
        "default_value": args.default_value or "",
        "description": args.description or "",
        "is_hidden": args.hidden,
    }
    result = client.request("POST", "/datasource_types/method_params/", json=data)
    print_json(result)


def cmd_update_param(args):
    """Update a method parameter."""
    client = GimsClient()
    data = {}

    if args.label:
        data["label"] = args.label
    if args.default_value is not None:
        data["default_value"] = args.default_value
    if args.description is not None:
        data["description"] = args.description
    if args.hidden is not None:
        data["is_hidden"] = args.hidden

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/datasource_types/method_params/{args.param_id}/", json=data)
    print_json(result)


def cmd_delete_param(args):
    """Delete a method parameter."""
    client = GimsClient()
    client.request("DELETE", f"/datasource_types/method_params/{args.param_id}/")
    print(f"Parameter {args.param_id} deleted successfully")


# ==================== Search ====================

def cmd_search(args):
    """Search datasource types by name or method code."""
    client = GimsClient()
    types = client.request("GET", "/datasource_types/ds_type/")

    results = []
    query = args.query.lower() if not args.case_sensitive else args.query

    for ds_type in types:
        name = ds_type["name"]
        name_check = name.lower() if not args.case_sensitive else name

        if args.search_in in ("name", "both") and query in name_check:
            results.append({
                "id": ds_type["id"],
                "name": name,
                "matched_in": "name",
            })
            continue

        if args.search_in in ("code", "both"):
            methods = client.request("GET", "/datasource_types/method/", params={"mds_type_id": ds_type["id"]})
            matched_methods = []
            for method in methods:
                code = method.get("code", "")
                code_check = code.lower() if not args.case_sensitive else code
                if query in code_check:
                    matched_methods.append({"id": method["id"], "name": method["name"]})

            if matched_methods:
                results.append({
                    "id": ds_type["id"],
                    "name": name,
                    "matched_in": "code",
                    "matched_methods": matched_methods,
                })

    print_json({"results": results, "count": len(results)})


def main():
    parser = argparse.ArgumentParser(
        description="GIMS DataSource Types CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Folders
    subparsers.add_parser("list-folders", help="List all folders")

    create_folder = subparsers.add_parser("create-folder", help="Create a folder")
    create_folder.add_argument("--name", required=True, help="Folder name")
    create_folder.add_argument("--parent-folder-id", type=int, help="Parent folder ID")

    delete_folder = subparsers.add_parser("delete-folder", help="Delete a folder")
    delete_folder.add_argument("folder_id", type=int, help="Folder ID")

    # Types
    subparsers.add_parser("list", help="List all datasource types")

    get_cmd = subparsers.add_parser("get", help="Get a datasource type")
    get_cmd.add_argument("type_id", type=int, help="Type ID")
    get_cmd.add_argument("--no-properties", dest="include_properties", action="store_false", help="Exclude properties")
    get_cmd.add_argument("--no-methods", dest="include_methods", action="store_false", help="Exclude methods")
    get_cmd.set_defaults(include_properties=True, include_methods=True)

    create_cmd = subparsers.add_parser("create", help="Create a datasource type")
    create_cmd.add_argument("--name", required=True, help="Type name")
    create_cmd.add_argument("--description", help="Description")
    create_cmd.add_argument("--version", help="Version (default: 1.0)")
    create_cmd.add_argument("--folder-id", type=int, help="Folder ID")

    update_cmd = subparsers.add_parser("update", help="Update a datasource type")
    update_cmd.add_argument("type_id", type=int, help="Type ID")
    update_cmd.add_argument("--name", help="New name")
    update_cmd.add_argument("--description", help="New description")
    update_cmd.add_argument("--version", help="New version")
    update_cmd.add_argument("--folder-id", type=int, help="New folder ID (0 to remove)")

    delete_cmd = subparsers.add_parser("delete", help="Delete a datasource type")
    delete_cmd.add_argument("type_id", type=int, help="Type ID")

    # Properties
    list_props = subparsers.add_parser("list-properties", help="List properties of a type")
    list_props.add_argument("type_id", type=int, help="Type ID")

    create_prop = subparsers.add_parser("create-property", help="Create a property")
    create_prop.add_argument("--type-id", type=int, required=True, help="Type ID")
    create_prop.add_argument("--name", required=True, help="Property display name")
    create_prop.add_argument("--label", required=True, help="Property label (code variable)")
    create_prop.add_argument("--value-type-id", type=int, required=True, help="Value type ID")
    create_prop.add_argument("--section-id", type=int, required=True, help="Section ID")
    create_prop.add_argument("--description", help="Description")
    create_prop.add_argument("--default-value", help="Default value")
    create_prop.add_argument("--required", action="store_true", help="Is required")
    create_prop.add_argument("--hidden", action="store_true", help="Is hidden")

    update_prop = subparsers.add_parser("update-property", help="Update a property")
    update_prop.add_argument("property_id", type=int, help="Property ID")
    update_prop.add_argument("--name", help="New name")
    update_prop.add_argument("--label", help="New label")
    update_prop.add_argument("--description", help="New description")
    update_prop.add_argument("--default-value", help="New default value")
    update_prop.add_argument("--required", type=lambda x: x.lower() == "true", help="Is required (true/false)")
    update_prop.add_argument("--hidden", type=lambda x: x.lower() == "true", help="Is hidden (true/false)")

    delete_prop = subparsers.add_parser("delete-property", help="Delete a property")
    delete_prop.add_argument("property_id", type=int, help="Property ID")

    # Methods
    list_methods = subparsers.add_parser("list-methods", help="List methods of a type")
    list_methods.add_argument("type_id", type=int, help="Type ID")

    get_method = subparsers.add_parser("get-method", help="Get method metadata")
    get_method.add_argument("method_id", type=int, help="Method ID")

    get_method_code = subparsers.add_parser("get-method-code", help="Get method code")
    get_method_code.add_argument("method_id", type=int, help="Method ID")

    create_method = subparsers.add_parser("create-method", help="Create a method")
    create_method.add_argument("--type-id", type=int, required=True, help="Type ID")
    create_method.add_argument("--name", required=True, help="Method name")
    create_method.add_argument("--label", required=True, help="Method label")
    create_method.add_argument("--code", help="Method code")
    create_method.add_argument("--code-file", help="Read code from file")
    create_method.add_argument("--description", help="Description")

    update_method = subparsers.add_parser("update-method", help="Update a method")
    update_method.add_argument("method_id", type=int, help="Method ID")
    update_method.add_argument("--name", help="New name")
    update_method.add_argument("--label", help="New label")
    update_method.add_argument("--code", help="New code")
    update_method.add_argument("--code-file", help="Read code from file")
    update_method.add_argument("--description", help="New description")

    delete_method = subparsers.add_parser("delete-method", help="Delete a method")
    delete_method.add_argument("method_id", type=int, help="Method ID")

    # Method Parameters
    list_params = subparsers.add_parser("list-params", help="List method parameters")
    list_params.add_argument("method_id", type=int, help="Method ID")

    create_param = subparsers.add_parser("create-param", help="Create a method parameter")
    create_param.add_argument("--method-id", type=int, required=True, help="Method ID")
    create_param.add_argument("--label", required=True, help="Parameter label")
    create_param.add_argument("--value-type-id", type=int, required=True, help="Value type ID")
    create_param.add_argument("--input", action="store_true", default=True, help="Input parameter (default)")
    create_param.add_argument("--output", dest="input", action="store_false", help="Output parameter")
    create_param.add_argument("--default-value", help="Default value")
    create_param.add_argument("--description", help="Description")
    create_param.add_argument("--hidden", action="store_true", help="Is hidden")

    update_param = subparsers.add_parser("update-param", help="Update a method parameter")
    update_param.add_argument("param_id", type=int, help="Parameter ID")
    update_param.add_argument("--label", help="New label")
    update_param.add_argument("--default-value", help="New default value")
    update_param.add_argument("--description", help="New description")
    update_param.add_argument("--hidden", type=lambda x: x.lower() == "true", help="Is hidden (true/false)")

    delete_param = subparsers.add_parser("delete-param", help="Delete a method parameter")
    delete_param.add_argument("param_id", type=int, help="Parameter ID")

    # Search
    search_cmd = subparsers.add_parser("search", help="Search datasource types")
    search_cmd.add_argument("--query", required=True, help="Search query")
    search_cmd.add_argument("--search-in", choices=["name", "code", "both"], default="name", help="Where to search")
    search_cmd.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")

    args = parser.parse_args()

    try:
        handlers = {
            "list-folders": cmd_list_folders,
            "create-folder": cmd_create_folder,
            "delete-folder": cmd_delete_folder,
            "list": cmd_list,
            "get": cmd_get,
            "create": cmd_create,
            "update": cmd_update,
            "delete": cmd_delete,
            "list-properties": cmd_list_properties,
            "create-property": cmd_create_property,
            "update-property": cmd_update_property,
            "delete-property": cmd_delete_property,
            "list-methods": cmd_list_methods,
            "get-method": cmd_get_method,
            "get-method-code": cmd_get_method_code,
            "create-method": cmd_create_method,
            "update-method": cmd_update_method,
            "delete-method": cmd_delete_method,
            "list-params": cmd_list_params,
            "create-param": cmd_create_param,
            "update-param": cmd_update_param,
            "delete-param": cmd_delete_param,
            "search": cmd_search,
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
