#!/usr/bin/env python3
"""CLI for GIMS Scripts management."""

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


def cmd_list_folders(args):
    """List all script folders."""
    client = GimsClient()
    folders = client.request("GET", "/scripts/folder/")
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
    """Create a script folder."""
    client = GimsClient()
    data = {"name": args.name}
    if args.parent_folder_id:
        data["parent_folder_id"] = args.parent_folder_id
    result = client.request("POST", "/scripts/folder/", json=data)
    print_json(result)


def cmd_delete_folder(args):
    """Delete a script folder."""
    client = GimsClient()
    client.request("DELETE", f"/scripts/folder/{args.folder_id}/")
    print(f"Folder {args.folder_id} deleted successfully")


def cmd_list(args):
    """List all scripts."""
    client = GimsClient()
    folders = client.request("GET", "/scripts/folder/")
    paths = build_folder_paths(folders)

    scripts = client.request("GET", "/scripts/script/")

    if args.folder_id:
        scripts = [s for s in scripts if s.get("folder_id") == args.folder_id]

    result = []
    for script in scripts:
        folder_id = script.get("folder_id")
        result.append({
            "id": script["id"],
            "name": script["name"],
            "folder_path": paths.get(folder_id, "/") if folder_id else "/",
            "folder_id": folder_id,
        })

    print_json({"scripts": result})


def cmd_get(args):
    """Get a script by ID."""
    client = GimsClient()
    script = client.request("GET", f"/scripts/script/{args.script_id}/")

    if not args.include_code:
        script["code"] = "[FILTERED] Use --include-code to see code"

    print_json(script)


def cmd_get_code(args):
    """Get only script code."""
    client = GimsClient()
    script = client.request("GET", f"/scripts/script/{args.script_id}/")
    print(script.get("code", ""))


def cmd_create(args):
    """Create a script."""
    client = GimsClient()
    data = {"name": args.name}

    if args.code:
        data["code"] = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            data["code"] = f.read()
    else:
        data["code"] = ""

    if args.folder_id:
        data["folder_id"] = args.folder_id

    result = client.request("POST", "/scripts/script/", json=data)
    print_json(result)


def cmd_update(args):
    """Update a script."""
    client = GimsClient()
    data = {}

    if args.name:
        data["name"] = args.name

    if args.code:
        data["code"] = args.code
    elif args.code_file:
        with open(args.code_file) as f:
            data["code"] = f.read()

    if args.folder_id is not None:
        data["folder_id"] = args.folder_id if args.folder_id > 0 else None

    if not data:
        print_error("No changes specified")
        sys.exit(1)

    result = client.request("PATCH", f"/scripts/script/{args.script_id}/", json=data)
    print_json(result)


def cmd_delete(args):
    """Delete a script."""
    client = GimsClient()
    client.request("DELETE", f"/scripts/script/{args.script_id}/")
    print(f"Script {args.script_id} deleted successfully")


def cmd_search(args):
    """Search scripts by code."""
    client = GimsClient()
    params = {
        "search_code": args.query,
        "case_sensitive": "true" if args.case_sensitive else "false",
        "exact_match": "true" if args.exact_match else "false",
    }
    results = client.request("GET", "/scripts/search_code/", params=params)
    print_json({"results": results, "count": len(results)})


def main():
    parser = argparse.ArgumentParser(
        description="GIMS Scripts CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Folders
    subparsers.add_parser("list-folders", help="List all script folders")

    create_folder = subparsers.add_parser("create-folder", help="Create a folder")
    create_folder.add_argument("--name", required=True, help="Folder name")
    create_folder.add_argument("--parent-folder-id", type=int, help="Parent folder ID")

    delete_folder = subparsers.add_parser("delete-folder", help="Delete a folder")
    delete_folder.add_argument("folder_id", type=int, help="Folder ID")

    # Scripts
    list_cmd = subparsers.add_parser("list", help="List all scripts")
    list_cmd.add_argument("--folder-id", type=int, help="Filter by folder ID")

    get_cmd = subparsers.add_parser("get", help="Get a script")
    get_cmd.add_argument("script_id", type=int, help="Script ID")
    get_cmd.add_argument("--include-code", action="store_true", help="Include code in output")

    get_code = subparsers.add_parser("get-code", help="Get only script code")
    get_code.add_argument("script_id", type=int, help="Script ID")

    create_cmd = subparsers.add_parser("create", help="Create a script")
    create_cmd.add_argument("--name", required=True, help="Script name")
    create_cmd.add_argument("--code", help="Script code")
    create_cmd.add_argument("--code-file", help="Read code from file")
    create_cmd.add_argument("--folder-id", type=int, help="Folder ID")

    update_cmd = subparsers.add_parser("update", help="Update a script")
    update_cmd.add_argument("script_id", type=int, help="Script ID")
    update_cmd.add_argument("--name", help="New name")
    update_cmd.add_argument("--code", help="New code")
    update_cmd.add_argument("--code-file", help="Read code from file")
    update_cmd.add_argument("--folder-id", type=int, help="New folder ID (0 to remove)")

    delete_cmd = subparsers.add_parser("delete", help="Delete a script")
    delete_cmd.add_argument("script_id", type=int, help="Script ID")

    search_cmd = subparsers.add_parser("search", help="Search scripts by code")
    search_cmd.add_argument("--query", required=True, help="Search query")
    search_cmd.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    search_cmd.add_argument("--exact-match", action="store_true", help="Exact match")

    args = parser.parse_args()

    try:
        handlers = {
            "list-folders": cmd_list_folders,
            "create-folder": cmd_create_folder,
            "delete-folder": cmd_delete_folder,
            "list": cmd_list,
            "get": cmd_get,
            "get-code": cmd_get_code,
            "create": cmd_create,
            "update": cmd_update,
            "delete": cmd_delete,
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
