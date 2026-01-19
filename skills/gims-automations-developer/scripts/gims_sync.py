#!/usr/bin/env python3
"""
CLI for GIMS Local-First Workflow - checkout/publish components.

Key principle: Code is NEVER loaded into LLM context.
- checkout: writes code to files, returns only metadata JSON
- publish: reads code from files, sends to GIMS, returns status JSON

Git = source of truth, GIMS = deployment target.
"""

import argparse
import ast
import io
import json
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from types import SimpleNamespace

import yaml

from gims_client import GimsClient, GimsApiError, print_error, print_json


# ==================== Serializers ====================


def serialize_script(script_data: dict, gims_url: str) -> tuple[str, str]:
    """Serialize script to meta.yaml and code.py format."""
    meta = {
        "gims_id": script_data["id"],
        "name": script_data["name"],
        "description": script_data.get("description", ""),
        "version": "1.0",
        "gims_folder": script_data.get("folder_path", "/"),
        "gims_folder_id": script_data.get("folder_id"),
        "code_file": "code.py",
        "gims_updated_at": script_data.get("updated_at"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }

    return yaml.dump(meta, allow_unicode=True, default_flow_style=False), script_data.get("code", "")


def serialize_datasource_type(type_data: dict, methods: list, properties: list, gims_url: str) -> dict[str, str]:
    """Serialize datasource type with methods and properties."""
    files = {}

    # meta.yaml
    meta = {
        "gims_id": type_data["id"],
        "name": type_data["name"],
        "description": type_data.get("description", ""),
        "version": type_data.get("version", "1.0"),
        "gims_folder": type_data.get("folder_path", "/"),
        "gims_folder_id": type_data.get("folder_id"),
        "gims_updated_at": type_data.get("updated_at"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }
    files["meta.yaml"] = yaml.dump(meta, allow_unicode=True, default_flow_style=False)

    # properties.yaml
    props = {"properties": [serialize_property(p) for p in properties]}
    files["properties.yaml"] = yaml.dump(props, allow_unicode=True, default_flow_style=False)

    # methods/
    for method in methods:
        method_folder = f"methods/{method['label']}"
        method_meta = {
            "gims_id": method["id"],
            "name": method["name"],
            "label": method["label"],
            "description": method.get("description", ""),
            "code_file": "code.py",
            "params_file": "params.yaml",
            "gims_updated_at": method.get("updated_at"),
        }
        files[f"{method_folder}/meta.yaml"] = yaml.dump(method_meta, allow_unicode=True, default_flow_style=False)
        files[f"{method_folder}/code.py"] = method.get("code", "# No code")

        params = {"parameters": [serialize_parameter(p) for p in method.get("parameters", [])]}
        files[f"{method_folder}/params.yaml"] = yaml.dump(params, allow_unicode=True, default_flow_style=False)

    return files


def serialize_activator_type(type_data: dict, properties: list, gims_url: str) -> dict[str, str]:
    """Serialize activator type with properties and code."""
    files = {}

    # meta.yaml
    meta = {
        "gims_id": type_data["id"],
        "name": type_data["name"],
        "description": type_data.get("description", ""),
        "version": type_data.get("version", "1.0"),
        "gims_folder": type_data.get("folder_path", "/"),
        "gims_folder_id": type_data.get("folder_id"),
        "code_file": "code.py",
        "gims_updated_at": type_data.get("updated_at"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }
    files["meta.yaml"] = yaml.dump(meta, allow_unicode=True, default_flow_style=False)

    # code.py
    files["code.py"] = type_data.get("code", "# No code")

    # properties.yaml
    props = {"properties": [serialize_property(p) for p in properties]}
    files["properties.yaml"] = yaml.dump(props, allow_unicode=True, default_flow_style=False)

    return files


def serialize_property(prop: dict) -> dict:
    """Serialize a property for YAML export."""
    result = {
        "gims_id": prop.get("id"),
        "name": prop["name"],
        "label": prop["label"],
        "value_type": prop.get("value_type_name", prop.get("value_type", "")),
        "value_type_id": prop.get("value_type_id"),
        "default_value": prop.get("default_value", ""),
        "section": prop.get("section_name", prop.get("section", "Основные")),
        "section_id": prop.get("section_name_id"),
        "is_required": prop.get("is_required", False),
        "is_hidden": prop.get("is_hidden", False),
        "is_inner": prop.get("is_inner", False),
        "description": prop.get("description", ""),
    }
    return result


def serialize_parameter(param: dict) -> dict:
    """Serialize a method parameter for YAML export."""
    return {
        "gims_id": param.get("id"),
        "label": param["label"],
        "input_type": param.get("input_type", True),
        "value_type": param.get("value_type_name", param.get("value_type", "")),
        "value_type_id": param.get("value_type_id"),
        "default_value": param.get("default_value", ""),
        "description": param.get("description", ""),
        "is_hidden": param.get("is_hidden", False),
    }


# ==================== Deserializers ====================


def deserialize_property(prop: dict) -> dict:
    """Deserialize property from YAML to GIMS API format."""
    return {
        "name": prop["name"],
        "label": prop["label"],
        "value_type_id": prop.get("value_type_id"),
        "default_value": prop.get("default_value", ""),
        "section_name_id": prop.get("section_id"),
        "is_required": prop.get("is_required", False),
        "is_hidden": prop.get("is_hidden", False),
        "is_inner": prop.get("is_inner", False),
        "description": prop.get("description", ""),
    }


def deserialize_parameter(param: dict) -> dict:
    """Deserialize method parameter from YAML to GIMS API format."""
    return {
        "label": param["label"],
        "input_type": param.get("input_type", True),
        "value_type_id": param.get("value_type_id"),
        "default_value": param.get("default_value", ""),
        "description": param.get("description", ""),
        "is_hidden": param.get("is_hidden", False),
    }


# ==================== Validators ====================


def validate_python_syntax(code: str) -> tuple[bool, str | None]:
    """Validate Python code syntax using ast.parse()."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Синтаксическая ошибка в строке {e.lineno}: {e.msg}"


# ==================== Helpers ====================


def fuzzy_match(name1: str, name2: str) -> float:
    """Calculate fuzzy match ratio between two strings."""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()


def find_similar_components(client: GimsClient, name: str, component_type: str, threshold: float = 0.6) -> list[dict]:
    """Find components with similar names."""
    if component_type == "script":
        components = client.request("GET", "/scripts/script/")
    elif component_type == "datasource_type":
        components = client.request("GET", "/datasource_types/ds_type/")
    elif component_type == "activator_type":
        components = client.request("GET", "/activator_types/activator_type/")
    else:
        return []

    matches = []
    for comp in components:
        ratio = fuzzy_match(name, comp["name"])
        if ratio >= threshold:
            matches.append({
                "gims_id": comp["id"],
                "name": comp["name"],
                "match_ratio": round(ratio, 2),
            })

    return sorted(matches, key=lambda x: x["match_ratio"], reverse=True)


def count_code_lines(code: str) -> int:
    """Count non-empty lines in code."""
    return len([line for line in code.split("\n") if line.strip()])


def detect_component_type(input_dir: Path) -> str | None:
    """Detect component type based on directory structure."""
    if (input_dir / "methods").is_dir():
        return "datasource_type"
    if (input_dir / "code.py").exists() and (input_dir / "properties.yaml").exists():
        return "activator_type"
    if (input_dir / "code.py").exists() and (input_dir / "meta.yaml").exists():
        return "script"
    return None


def compare_properties(local_props: list[dict], gims_props: list[dict]) -> dict:
    """Compare local and GIMS properties, return changes."""
    local_by_label = {p["label"]: p for p in local_props}
    gims_by_label = {p["label"]: p for p in gims_props}

    to_add = []
    to_update = []
    to_delete = []

    # Check local properties
    for label, local_prop in local_by_label.items():
        if label not in gims_by_label:
            to_add.append(label)
        else:
            gims_prop = gims_by_label[label]
            # Compare relevant fields
            if (local_prop.get("name") != gims_prop.get("name") or
                local_prop.get("default_value") != gims_prop.get("default_value") or
                local_prop.get("is_required") != gims_prop.get("is_required") or
                local_prop.get("description") != gims_prop.get("description")):
                to_update.append(label)

    # Check for deletions
    for label in gims_by_label:
        if label not in local_by_label:
            to_delete.append(label)

    return {"add": to_add, "update": to_update, "delete": to_delete}


def compare_parameters(local_params: list[dict], gims_params: list[dict]) -> dict:
    """Compare local and GIMS method parameters, return changes."""
    local_by_label = {p["label"]: p for p in local_params}
    gims_by_label = {p["label"]: p for p in gims_params}

    return {
        "add": [l for l in local_by_label if l not in gims_by_label],
        "update": [l for l in local_by_label if l in gims_by_label],
        "delete": [l for l in gims_by_label if l not in local_by_label],
    }


# ==================== Checkout Commands ====================


def cmd_checkout(args):
    """Checkout component from GIMS to local files."""
    client = GimsClient()
    component_type = args.component_type

    if component_type == "script":
        return _checkout_script(client, args)
    elif component_type == "datasource_type":
        return _checkout_datasource_type(client, args)
    elif component_type == "activator_type":
        return _checkout_activator_type(client, args)
    else:
        print_error(f"Неизвестный тип компонента: {component_type}")
        sys.exit(1)


def _checkout_script(client: GimsClient, args):
    """Checkout script from GIMS."""
    # Find script
    if args.id:
        script = client.request("GET", f"/scripts/script/{args.id}/")
    elif args.name:
        scripts = client.request("GET", "/scripts/script/")
        script = next((s for s in scripts if s["name"] == args.name), None)
        if not script:
            print_json({"status": "error", "message": f"Скрипт '{args.name}' не найден"})
            sys.exit(1)
        script = client.request("GET", f"/scripts/script/{script['id']}/")
    else:
        print_error("Укажите --id или --name")
        sys.exit(1)

    # Serialize
    meta_yaml, code = serialize_script(script, client.gims_url)

    # Output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(script["name"].lower().replace(" ", "_"))

    if args.dry_run:
        print_json({
            "status": "dry_run",
            "gims_id": script["id"],
            "name": script["name"],
            "output_dir": str(output_dir),
            "files": ["meta.yaml", "code.py"],
            "code_lines": count_code_lines(code),
        })
        return

    # Check for existing files
    if output_dir.exists() and not args.force:
        meta_file = output_dir / "meta.yaml"
        if meta_file.exists():
            local_meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            local_updated = local_meta.get("gims_updated_at")
            gims_updated = script.get("updated_at")

            if local_updated and gims_updated and local_updated != gims_updated:
                print_json({
                    "status": "conflict",
                    "gims_id": script["id"],
                    "name": script["name"],
                    "local_updated_at": local_updated,
                    "gims_updated_at": gims_updated,
                    "message": "Локальные файлы могут содержать несохранённые изменения",
                    "recommendation": "Используйте --force для перезаписи или publish для сохранения в GIMS",
                })
                sys.exit(1)

    # Write files
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "meta.yaml").write_text(meta_yaml, encoding="utf-8")
    (output_dir / "code.py").write_text(code, encoding="utf-8")

    print_json({
        "status": "checked_out",
        "gims_id": script["id"],
        "name": script["name"],
        "output_dir": str(output_dir),
        "files": ["meta.yaml", "code.py"],
        "code_lines": count_code_lines(code),
        "gims_updated_at": script.get("updated_at"),
    })


def _checkout_datasource_type(client: GimsClient, args):
    """Checkout datasource type from GIMS."""
    # Find type
    if args.id:
        ds_type = client.request("GET", f"/datasource_types/ds_type/{args.id}/")
    elif args.name:
        types = client.request("GET", "/datasource_types/ds_type/")
        ds_type = next((t for t in types if t["name"] == args.name), None)
        if not ds_type:
            print_json({"status": "error", "message": f"Тип ИД '{args.name}' не найден"})
            sys.exit(1)
        ds_type = client.request("GET", f"/datasource_types/ds_type/{ds_type['id']}/")
    else:
        print_error("Укажите --id или --name")
        sys.exit(1)

    # Get properties and methods
    properties = client.request("GET", "/datasource_types/properties/", params={"mds_type_id": ds_type["id"]})
    methods = client.request("GET", "/datasource_types/method/", params={"mds_type_id": ds_type["id"]})

    # Get method parameters
    for method in methods:
        params = client.request("GET", "/datasource_types/method_params/", params={"method_id": method["id"]})
        method["parameters"] = params

    # Serialize
    files = serialize_datasource_type(ds_type, methods, properties, client.gims_url)

    # Output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(ds_type["name"].lower().replace(" ", "_"))

    if args.dry_run:
        print_json({
            "status": "dry_run",
            "gims_id": ds_type["id"],
            "name": ds_type["name"],
            "output_dir": str(output_dir),
            "files": list(files.keys()),
            "methods_count": len(methods),
            "properties_count": len(properties),
        })
        return

    # Write files
    for file_path, content in files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    print_json({
        "status": "checked_out",
        "gims_id": ds_type["id"],
        "name": ds_type["name"],
        "output_dir": str(output_dir),
        "files": list(files.keys()),
        "methods_count": len(methods),
        "properties_count": len(properties),
        "gims_updated_at": ds_type.get("updated_at"),
    })


def _checkout_activator_type(client: GimsClient, args):
    """Checkout activator type from GIMS."""
    # Find type
    if args.id:
        act_type = client.request("GET", f"/activator_types/activator_type/{args.id}/")
    elif args.name:
        types = client.request("GET", "/activator_types/activator_type/")
        act_type = next((t for t in types if t["name"] == args.name), None)
        if not act_type:
            print_json({"status": "error", "message": f"Тип активатора '{args.name}' не найден"})
            sys.exit(1)
        act_type = client.request("GET", f"/activator_types/activator_type/{act_type['id']}/")
    else:
        print_error("Укажите --id или --name")
        sys.exit(1)

    # Get properties
    all_properties = client.request("GET", "/activator_types/properties/")
    properties = [p for p in all_properties if p.get("activator_type_id") == act_type["id"]]

    # Serialize
    files = serialize_activator_type(act_type, properties, client.gims_url)

    # Output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(act_type["name"].lower().replace(" ", "_"))

    if args.dry_run:
        code = files.get("code.py", "")
        print_json({
            "status": "dry_run",
            "gims_id": act_type["id"],
            "name": act_type["name"],
            "output_dir": str(output_dir),
            "files": list(files.keys()),
            "code_lines": count_code_lines(code),
            "properties_count": len(properties),
        })
        return

    # Write files
    for file_path, content in files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

    print_json({
        "status": "checked_out",
        "gims_id": act_type["id"],
        "name": act_type["name"],
        "output_dir": str(output_dir),
        "files": list(files.keys()),
        "code_lines": count_code_lines(files.get("code.py", "")),
        "properties_count": len(properties),
        "gims_updated_at": act_type.get("updated_at"),
    })


def cmd_checkout_folder(args):
    """Checkout all components from a GIMS folder."""
    client = GimsClient()
    component_type = args.component_type
    output_base_dir = Path(args.output_base_dir) if args.output_base_dir else Path(".")

    # Get folder ID
    folder_id = None
    if args.folder_id:
        folder_id = args.folder_id
    elif args.folder_name:
        if component_type == "script":
            folders = client.request("GET", "/scripts/folder/")
        elif component_type == "datasource_type":
            folders = client.request("GET", "/datasource_types/folder/")
        elif component_type == "activator_type":
            folders = client.request("GET", "/activator_types/folder/")
        else:
            print_error(f"Неизвестный тип компонента: {component_type}")
            sys.exit(1)

        folder = next((f for f in folders if f["name"] == args.folder_name), None)
        if not folder:
            print_json({"status": "error", "message": f"Папка '{args.folder_name}' не найдена"})
            sys.exit(1)
        folder_id = folder["id"]

    # Get components in folder
    components: list = []
    if component_type == "script":
        components = client.request("GET", "/scripts/script/", params={"folder_id": folder_id} if folder_id else {})
    elif component_type == "datasource_type":
        components = client.request("GET", "/datasource_types/ds_type/", params={"folder_id": folder_id} if folder_id else {})
    elif component_type == "activator_type":
        components = client.request("GET", "/activator_types/activator_type/", params={"folder_id": folder_id} if folder_id else {})

    if args.dry_run:
        print_json({
            "status": "dry_run",
            "folder_id": folder_id,
            "folder_name": args.folder_name,
            "component_type": component_type,
            "components_count": len(components),
            "components": [{"gims_id": c["id"], "name": c["name"]} for c in components],
        })
        return

    # Checkout each component
    results = []
    for comp in components:
        output_dir = output_base_dir / comp["name"].lower().replace(" ", "_")

        # Create args-like object using SimpleNamespace
        checkout_args = SimpleNamespace(
            id=comp["id"],
            name=None,
            output_dir=str(output_dir),
            dry_run=False,
            force=args.force,
            component_type=component_type,
        )

        old_stdout = sys.stdout
        try:
            # Redirect stdout to capture JSON
            sys.stdout = io.StringIO()

            if component_type == "script":
                _checkout_script(client, checkout_args)
            elif component_type == "datasource_type":
                _checkout_datasource_type(client, checkout_args)
            elif component_type == "activator_type":
                _checkout_activator_type(client, checkout_args)

            output = sys.stdout.getvalue()
            result = json.loads(output)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "gims_id": comp["id"],
                "name": comp["name"],
                "error": str(e),
            })
        finally:
            sys.stdout = old_stdout

    print_json({
        "status": "checked_out",
        "folder_id": folder_id,
        "folder_name": args.folder_name,
        "component_type": component_type,
        "components": results,
    })


# ==================== Publish Commands ====================


def cmd_publish(args):
    """Publish local files to GIMS (two-stage: preview then confirm)."""
    client = GimsClient()
    input_dir = Path(args.input_dir)
    meta_file = input_dir / "meta.yaml"

    if not meta_file.exists():
        print_json({"status": "error", "message": f"Файл не найден: {meta_file}"})
        sys.exit(1)

    meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
    component_type = detect_component_type(input_dir)

    if not component_type:
        print_json({"status": "error", "message": "Не удалось определить тип компонента по структуре директории"})
        sys.exit(1)

    if component_type == "script":
        return _publish_script(client, input_dir, meta, args)
    elif component_type == "datasource_type":
        return _publish_datasource_type(client, input_dir, meta, args)
    elif component_type == "activator_type":
        return _publish_activator_type(client, input_dir, meta, args)


def _publish_script(client: GimsClient, input_dir: Path, meta: dict, args):
    """Publish script to GIMS."""
    code_file = input_dir / "code.py"
    if not code_file.exists():
        print_json({"status": "error", "message": f"Файл не найден: {code_file}"})
        sys.exit(1)

    code = code_file.read_text(encoding="utf-8")

    # Validate syntax
    is_valid, error = validate_python_syntax(code)
    if not is_valid:
        print_json({
            "status": "error",
            "message": "Ошибка синтаксиса Python",
            "detail": error,
        })
        sys.exit(1)

    gims_id = meta.get("gims_id")
    name = args.target_name or meta.get("name", "Unnamed Script")

    # Check if exists in GIMS
    existing = None
    if gims_id:
        try:
            existing = client.request("GET", f"/scripts/script/{gims_id}/")
        except GimsApiError as e:
            if e.status_code != 404:
                raise

    # Determine action
    if existing:
        action = "update"
        gims_code = existing.get("code", "")
        code_changed = gims_code != code

        if not args.confirm:
            # Stage 1: Show what will change
            print_json({
                "status": "pending_confirmation",
                "gims_id": gims_id,
                "name": name,
                "action": action,
                "changes": {
                    "code": "modified" if code_changed else "unchanged",
                },
                "local_lines": count_code_lines(code),
                "gims_lines": count_code_lines(gims_code),
            })
            return

        # Stage 2: Confirmed - execute
        if code_changed:
            client.request("PATCH", f"/scripts/script/{gims_id}/", json={"code": code})

        print_json({
            "status": "published",
            "gims_id": gims_id,
            "name": name,
            "action": "updated",
        })
    else:
        action = "create"

        if not args.confirm:
            # Stage 1: Show what will be created
            print_json({
                "status": "pending_confirmation",
                "gims_id": None,
                "name": name,
                "action": action,
                "folder_id": args.folder_id or meta.get("gims_folder_id"),
                "code_lines": count_code_lines(code),
            })
            return

        # Stage 2: Confirmed - create
        data = {"name": name, "code": code}
        folder_id = args.folder_id or meta.get("gims_folder_id")
        if folder_id:
            data["folder_id"] = folder_id

        result = client.request("POST", "/scripts/script/", json=data)

        # Update meta.yaml with new gims_id
        meta["gims_id"] = result["id"]
        meta["gims_updated_at"] = result.get("updated_at")
        meta_file = input_dir / "meta.yaml"
        meta_file.write_text(yaml.dump(meta, allow_unicode=True, default_flow_style=False), encoding="utf-8")

        print_json({
            "status": "published",
            "gims_id": result["id"],
            "name": name,
            "action": "created",
        })


def _publish_datasource_type(client: GimsClient, input_dir: Path, meta: dict, args):
    """Publish datasource type to GIMS."""
    gims_id = meta.get("gims_id")
    name = args.target_name or meta.get("name", "Unnamed DataSource Type")

    # Load local properties
    props_file = input_dir / "properties.yaml"
    local_props = []
    if props_file.exists():
        props_data = yaml.safe_load(props_file.read_text(encoding="utf-8"))
        local_props = props_data.get("properties", [])

    # Load local methods
    methods_dir = input_dir / "methods"
    local_methods = []
    if methods_dir.is_dir():
        for method_dir in methods_dir.iterdir():
            if method_dir.is_dir():
                method_meta_file = method_dir / "meta.yaml"
                method_code_file = method_dir / "code.py"
                method_params_file = method_dir / "params.yaml"

                if method_meta_file.exists():
                    method_meta = yaml.safe_load(method_meta_file.read_text(encoding="utf-8"))
                    method_meta["code"] = method_code_file.read_text(encoding="utf-8") if method_code_file.exists() else ""

                    if method_params_file.exists():
                        params_data = yaml.safe_load(method_params_file.read_text(encoding="utf-8"))
                        method_meta["parameters"] = params_data.get("parameters", [])
                    else:
                        method_meta["parameters"] = []

                    local_methods.append(method_meta)

    # Check if exists in GIMS
    existing = None
    if gims_id:
        try:
            existing = client.request("GET", f"/datasource_types/ds_type/{gims_id}/")
        except GimsApiError as e:
            if e.status_code != 404:
                raise

    if existing:
        action = "update"

        # Get current GIMS state
        gims_props = client.request("GET", "/datasource_types/properties/", params={"mds_type_id": gims_id})
        gims_methods = client.request("GET", "/datasource_types/method/", params={"mds_type_id": gims_id})

        # Compare
        prop_changes = compare_properties(local_props, gims_props)
        method_changes = {
            "add": [m["label"] for m in local_methods if not any(gm["label"] == m["label"] for gm in gims_methods)],
            "update": [m["label"] for m in local_methods if any(gm["label"] == m["label"] for gm in gims_methods)],
            "delete": [gm["label"] for gm in gims_methods if not any(m["label"] == gm["label"] for m in local_methods)],
        }

        requires_confirmation = []
        if prop_changes["delete"]:
            requires_confirmation.append(f"delete properties: {', '.join(prop_changes['delete'])}")
        if method_changes["delete"]:
            requires_confirmation.append(f"delete methods: {', '.join(method_changes['delete'])}")

        if not args.confirm:
            print_json({
                "status": "pending_confirmation",
                "gims_id": gims_id,
                "name": name,
                "action": action,
                "changes": {
                    "properties": prop_changes,
                    "methods": method_changes,
                },
                "requires_confirmation": requires_confirmation,
            })
            return

        # Execute updates
        # Update properties
        gims_props_by_label = {p["label"]: p for p in gims_props}
        local_props_by_label = {p["label"]: p for p in local_props}

        for label in prop_changes["add"]:
            prop_data = deserialize_property(local_props_by_label[label])
            prop_data["mds_type_id"] = gims_id
            client.request("POST", "/datasource_types/properties/", json=prop_data)

        for label in prop_changes["update"]:
            prop_id = gims_props_by_label[label]["id"]
            prop_data = deserialize_property(local_props_by_label[label])
            client.request("PATCH", f"/datasource_types/properties/{prop_id}/", json=prop_data)

        for label in prop_changes["delete"]:
            prop_id = gims_props_by_label[label]["id"]
            client.request("DELETE", f"/datasource_types/properties/{prop_id}/")

        # Update methods
        gims_methods_by_label = {m["label"]: m for m in gims_methods}
        local_methods_by_label = {m["label"]: m for m in local_methods}

        for label in method_changes["add"]:
            method_data = local_methods_by_label[label]
            # Validate code
            is_valid, error = validate_python_syntax(method_data.get("code", ""))
            if not is_valid:
                print_json({"status": "error", "message": f"Ошибка синтаксиса в методе {label}: {error}"})
                sys.exit(1)

            result = client.request("POST", "/datasource_types/method/", json={
                "mds_type_id": gims_id,
                "name": method_data["name"],
                "label": method_data["label"],
                "description": method_data.get("description", ""),
                "code": method_data.get("code", ""),
            })

            # Create parameters
            for param in method_data.get("parameters", []):
                param_data = deserialize_parameter(param)
                param_data["method_id"] = result["id"]
                client.request("POST", "/datasource_types/method_params/", json=param_data)

        for label in method_changes["update"]:
            method_id = gims_methods_by_label[label]["id"]
            method_data = local_methods_by_label[label]

            # Validate code
            is_valid, error = validate_python_syntax(method_data.get("code", ""))
            if not is_valid:
                print_json({"status": "error", "message": f"Ошибка синтаксиса в методе {label}: {error}"})
                sys.exit(1)

            client.request("PATCH", f"/datasource_types/method/{method_id}/", json={
                "name": method_data["name"],
                "description": method_data.get("description", ""),
                "code": method_data.get("code", ""),
            })

            # Update parameters
            gims_params = client.request("GET", "/datasource_types/method_params/", params={"method_id": method_id})
            gims_params_by_label = {p["label"]: p for p in gims_params}
            local_params_by_label = {p["label"]: p for p in method_data.get("parameters", [])}

            param_changes = compare_parameters(method_data.get("parameters", []), gims_params)

            for p_label in param_changes["add"]:
                param_data = deserialize_parameter(local_params_by_label[p_label])
                param_data["method_id"] = method_id
                client.request("POST", "/datasource_types/method_params/", json=param_data)

            for p_label in param_changes["update"]:
                param_id = gims_params_by_label[p_label]["id"]
                param_data = deserialize_parameter(local_params_by_label[p_label])
                client.request("PATCH", f"/datasource_types/method_params/{param_id}/", json=param_data)

            for p_label in param_changes["delete"]:
                param_id = gims_params_by_label[p_label]["id"]
                client.request("DELETE", f"/datasource_types/method_params/{param_id}/")

        for label in method_changes["delete"]:
            method_id = gims_methods_by_label[label]["id"]
            client.request("DELETE", f"/datasource_types/method/{method_id}/")

        print_json({
            "status": "published",
            "gims_id": gims_id,
            "name": name,
            "action": "updated",
            "changes_applied": {
                "properties": prop_changes,
                "methods": method_changes,
            },
        })
    else:
        action = "create"

        if not args.confirm:
            print_json({
                "status": "pending_confirmation",
                "gims_id": None,
                "name": name,
                "action": action,
                "folder_id": args.folder_id or meta.get("gims_folder_id"),
                "properties_count": len(local_props),
                "methods_count": len(local_methods),
            })
            return

        # Create type
        data = {
            "name": name,
            "description": meta.get("description", ""),
        }
        folder_id = args.folder_id or meta.get("gims_folder_id")
        if folder_id:
            data["folder_id"] = folder_id

        result = client.request("POST", "/datasource_types/ds_type/", json=data)
        new_gims_id = result["id"]

        # Create properties
        for prop in local_props:
            prop_data = deserialize_property(prop)
            prop_data["mds_type_id"] = new_gims_id
            client.request("POST", "/datasource_types/properties/", json=prop_data)

        # Create methods
        for method_data in local_methods:
            is_valid, error = validate_python_syntax(method_data.get("code", ""))
            if not is_valid:
                print_json({"status": "error", "message": f"Ошибка синтаксиса в методе {method_data['label']}: {error}"})
                sys.exit(1)

            method_result = client.request("POST", "/datasource_types/method/", json={
                "mds_type_id": new_gims_id,
                "name": method_data["name"],
                "label": method_data["label"],
                "description": method_data.get("description", ""),
                "code": method_data.get("code", ""),
            })

            for param in method_data.get("parameters", []):
                param_data = deserialize_parameter(param)
                param_data["method_id"] = method_result["id"]
                client.request("POST", "/datasource_types/method_params/", json=param_data)

        # Update meta.yaml
        meta["gims_id"] = new_gims_id
        meta["gims_updated_at"] = result.get("updated_at")
        meta_file = input_dir / "meta.yaml"
        meta_file.write_text(yaml.dump(meta, allow_unicode=True, default_flow_style=False), encoding="utf-8")

        print_json({
            "status": "published",
            "gims_id": new_gims_id,
            "name": name,
            "action": "created",
        })


def _publish_activator_type(client: GimsClient, input_dir: Path, meta: dict, args):
    """Publish activator type to GIMS."""
    code_file = input_dir / "code.py"
    if not code_file.exists():
        print_json({"status": "error", "message": f"Файл не найден: {code_file}"})
        sys.exit(1)

    code = code_file.read_text(encoding="utf-8")

    # Validate syntax
    is_valid, error = validate_python_syntax(code)
    if not is_valid:
        print_json({
            "status": "error",
            "message": "Ошибка синтаксиса Python",
            "detail": error,
        })
        sys.exit(1)

    gims_id = meta.get("gims_id")
    name = args.target_name or meta.get("name", "Unnamed Activator Type")

    # Load local properties
    props_file = input_dir / "properties.yaml"
    local_props = []
    if props_file.exists():
        props_data = yaml.safe_load(props_file.read_text(encoding="utf-8"))
        local_props = props_data.get("properties", [])

    # Check if exists in GIMS
    existing = None
    if gims_id:
        try:
            existing = client.request("GET", f"/activator_types/activator_type/{gims_id}/")
        except GimsApiError as e:
            if e.status_code != 404:
                raise

    if existing:
        action = "update"

        # Get current GIMS state
        all_gims_props = client.request("GET", "/activator_types/properties/")
        gims_props = [p for p in all_gims_props if p.get("activator_type_id") == gims_id]

        gims_code = existing.get("code", "")
        code_changed = gims_code != code

        # Compare properties
        prop_changes = compare_properties(local_props, gims_props)

        requires_confirmation = []
        if prop_changes["delete"]:
            requires_confirmation.append(f"delete properties: {', '.join(prop_changes['delete'])}")

        if not args.confirm:
            print_json({
                "status": "pending_confirmation",
                "gims_id": gims_id,
                "name": name,
                "action": action,
                "changes": {
                    "code": "modified" if code_changed else "unchanged",
                    "properties": prop_changes,
                },
                "requires_confirmation": requires_confirmation,
            })
            return

        # Execute updates
        if code_changed:
            client.request("PATCH", f"/activator_types/activator_type/{gims_id}/", json={"code": code})

        # Update properties
        gims_props_by_label = {p["label"]: p for p in gims_props}
        local_props_by_label = {p["label"]: p for p in local_props}

        for label in prop_changes["add"]:
            prop_data = deserialize_property(local_props_by_label[label])
            prop_data["activator_type_id"] = gims_id
            client.request("POST", "/activator_types/properties/", json=prop_data)

        for label in prop_changes["update"]:
            prop_id = gims_props_by_label[label]["id"]
            prop_data = deserialize_property(local_props_by_label[label])
            client.request("PATCH", f"/activator_types/properties/{prop_id}/", json=prop_data)

        for label in prop_changes["delete"]:
            prop_id = gims_props_by_label[label]["id"]
            client.request("DELETE", f"/activator_types/properties/{prop_id}/")

        print_json({
            "status": "published",
            "gims_id": gims_id,
            "name": name,
            "action": "updated",
            "changes_applied": {
                "code": "updated" if code_changed else "unchanged",
                "properties": prop_changes,
            },
        })
    else:
        action = "create"

        if not args.confirm:
            print_json({
                "status": "pending_confirmation",
                "gims_id": None,
                "name": name,
                "action": action,
                "folder_id": args.folder_id or meta.get("gims_folder_id"),
                "code_lines": count_code_lines(code),
                "properties_count": len(local_props),
            })
            return

        # Create type
        data = {
            "name": name,
            "description": meta.get("description", ""),
            "code": code,
        }
        folder_id = args.folder_id or meta.get("gims_folder_id")
        if folder_id:
            data["folder_id"] = folder_id

        result = client.request("POST", "/activator_types/activator_type/", json=data)
        new_gims_id = result["id"]

        # Create properties
        for prop in local_props:
            prop_data = deserialize_property(prop)
            prop_data["activator_type_id"] = new_gims_id
            client.request("POST", "/activator_types/properties/", json=prop_data)

        # Update meta.yaml
        meta["gims_id"] = new_gims_id
        meta["gims_updated_at"] = result.get("updated_at")
        meta_file = input_dir / "meta.yaml"
        meta_file.write_text(yaml.dump(meta, allow_unicode=True, default_flow_style=False), encoding="utf-8")

        print_json({
            "status": "published",
            "gims_id": new_gims_id,
            "name": name,
            "action": "created",
        })


def cmd_publish_all(args):
    """Publish all modified components from a base directory."""
    client = GimsClient()
    base_dir = Path(args.base_dir)

    if not base_dir.is_dir():
        print_json({"status": "error", "message": f"Директория не найдена: {base_dir}"})
        sys.exit(1)

    # Find all component directories
    components = []
    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            meta_file = subdir / "meta.yaml"
            if meta_file.exists():
                meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
                component_type = detect_component_type(subdir)
                if component_type:
                    components.append({
                        "path": str(subdir),
                        "name": meta.get("name"),
                        "gims_id": meta.get("gims_id"),
                        "component_type": component_type,
                    })

    if args.dry_run:
        print_json({
            "status": "dry_run",
            "base_dir": str(base_dir),
            "components": components,
        })
        return

    if not args.confirm:
        print_json({
            "status": "pending_confirmation",
            "base_dir": str(base_dir),
            "components": components,
            "message": "Добавьте --confirm для выполнения publish всех компонентов",
        })
        return

    # Publish each component
    results = []
    for comp in components:
        # Create args-like object using SimpleNamespace
        publish_args = SimpleNamespace(
            input_dir=comp["path"],
            target_name=None,
            folder_id=None,
            confirm=True,
            force=args.force,
        )

        old_stdout = sys.stdout
        try:
            # Redirect stdout
            sys.stdout = io.StringIO()

            if comp["component_type"] == "script":
                _publish_script(client, Path(comp["path"]), yaml.safe_load(Path(comp["path"], "meta.yaml").read_text()), publish_args)
            elif comp["component_type"] == "datasource_type":
                _publish_datasource_type(client, Path(comp["path"]), yaml.safe_load(Path(comp["path"], "meta.yaml").read_text()), publish_args)
            elif comp["component_type"] == "activator_type":
                _publish_activator_type(client, Path(comp["path"]), yaml.safe_load(Path(comp["path"], "meta.yaml").read_text()), publish_args)

            output = sys.stdout.getvalue()
            result = json.loads(output)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "name": comp["name"],
                "path": comp["path"],
                "error": str(e),
            })
        finally:
            sys.stdout = old_stdout

    # Check for errors
    errors = [r for r in results if r.get("status") == "error"]
    if errors and not args.force:
        print_json({
            "status": "error",
            "message": "Publish прерван из-за ошибок",
            "errors": errors,
            "successful": [r for r in results if r.get("status") != "error"],
        })
        sys.exit(1)

    print_json({
        "status": "published",
        "base_dir": str(base_dir),
        "results": results,
    })


# ==================== Status Command ====================


def cmd_status(args):
    """Show status of local components vs GIMS."""
    client = GimsClient()
    base_dir = Path(args.base_dir)

    if not base_dir.is_dir():
        print_json({"status": "error", "message": f"Директория не найдена: {base_dir}"})
        sys.exit(1)

    components = []

    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            meta_file = subdir / "meta.yaml"
            if meta_file.exists():
                meta = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
                component_type = detect_component_type(subdir)
                gims_id = meta.get("gims_id")
                local_updated = meta.get("gims_updated_at")

                status = "unknown"
                gims_updated = None

                if not gims_id:
                    status = "local_only"
                else:
                    # Get GIMS version
                    try:
                        if component_type == "script":
                            gims_comp = client.request("GET", f"/scripts/script/{gims_id}/")
                        elif component_type == "datasource_type":
                            gims_comp = client.request("GET", f"/datasource_types/ds_type/{gims_id}/")
                        elif component_type == "activator_type":
                            gims_comp = client.request("GET", f"/activator_types/activator_type/{gims_id}/")
                        else:
                            gims_comp = None

                        if gims_comp:
                            gims_updated = gims_comp.get("updated_at")
                            if local_updated == gims_updated:
                                status = "in_sync"
                            elif local_updated and gims_updated:
                                # Compare timestamps
                                try:
                                    local_dt = datetime.fromisoformat(local_updated.replace("Z", "+00:00"))
                                    gims_dt = datetime.fromisoformat(gims_updated.replace("Z", "+00:00"))
                                    if local_dt > gims_dt:
                                        status = "local_newer"
                                    else:
                                        status = "gims_newer"
                                except ValueError:
                                    status = "unknown"
                            else:
                                status = "unknown"
                    except GimsApiError as e:
                        if e.status_code == 404:
                            status = "gims_deleted"
                        else:
                            status = "error"

                components.append({
                    "name": meta.get("name"),
                    "gims_id": gims_id,
                    "component_type": component_type,
                    "status": status,
                    "path": str(subdir),
                    "local_updated_at": local_updated,
                    "gims_updated_at": gims_updated,
                })

    print_json({
        "base_dir": str(base_dir),
        "components": components,
        "summary": {
            "total": len(components),
            "in_sync": len([c for c in components if c["status"] == "in_sync"]),
            "local_newer": len([c for c in components if c["status"] == "local_newer"]),
            "gims_newer": len([c for c in components if c["status"] == "gims_newer"]),
            "local_only": len([c for c in components if c["status"] == "local_only"]),
            "gims_deleted": len([c for c in components if c["status"] == "gims_deleted"]),
        },
    })


# ==================== Other Commands ====================


def cmd_validate_code(args):
    """Validate Python code syntax."""
    if args.file:
        code = Path(args.file).read_text(encoding="utf-8")
    elif args.code:
        code = args.code
    else:
        print_error("Укажите --file или --code")
        sys.exit(1)

    is_valid, error = validate_python_syntax(code)
    print_json({
        "valid": is_valid,
        "error": error,
    })

    if not is_valid:
        sys.exit(1)


def cmd_find_duplicates(args):
    """Find components with similar names."""
    client = GimsClient()
    name = args.name
    component_type = args.component_type
    threshold = args.threshold

    matches = find_similar_components(client, name, component_type, threshold)

    print_json({
        "query": name,
        "component_type": component_type,
        "threshold": threshold,
        "matches": matches,
    })


def cmd_compare(args):
    """Compare GIMS component with Git version."""
    client = GimsClient()

    # Parse git date
    try:
        git_date = datetime.fromisoformat(args.git_exported_at.replace("Z", "+00:00"))
    except ValueError as e:
        print_json({"status": "error", "message": f"Неверный формат даты: {e}"})
        sys.exit(1)

    # Get component from GIMS
    if args.component_type == "script":
        components = client.request("GET", "/scripts/script/")
        component = next((c for c in components if c["name"] == args.gims_name), None)
    elif args.component_type == "datasource_type":
        components = client.request("GET", "/datasource_types/ds_type/")
        component = next((c for c in components if c["name"] == args.gims_name), None)
    elif args.component_type == "activator_type":
        components = client.request("GET", "/activator_types/activator_type/")
        component = next((c for c in components if c["name"] == args.gims_name), None)
    else:
        print_json({"status": "error", "message": f"Неизвестный тип компонента: {args.component_type}"})
        sys.exit(1)

    if not component:
        print_json({
            "status": "not_found_in_gims",
            "recommendation": "publish",
            "message": f"Компонент '{args.gims_name}' не найден в GIMS. Рекомендуется publish.",
        })
        return

    # Compare dates
    gims_updated_at = component.get("updated_at")
    if not gims_updated_at:
        print_json({
            "status": "no_updated_at",
            "message": "Компонент в GIMS не имеет поля updated_at. Невозможно сравнить.",
            "recommendation": "manual_check",
        })
        return

    try:
        gims_date = datetime.fromisoformat(gims_updated_at.replace("Z", "+00:00"))
    except ValueError:
        print_json({
            "status": "invalid_gims_date",
            "message": f"Некорректный формат даты в GIMS: {gims_updated_at}",
            "recommendation": "manual_check",
        })
        return

    if gims_date > git_date:
        print_json({
            "status": "gims_newer",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": args.git_exported_at,
            "recommendation": "checkout",
            "message": "Версия в GIMS новее. Рекомендуется checkout в Git.",
        })
    elif gims_date < git_date:
        print_json({
            "status": "git_newer",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": args.git_exported_at,
            "recommendation": "publish",
            "message": "Версия в Git новее. Рекомендуется publish в GIMS.",
        })
    else:
        print_json({
            "status": "in_sync",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": args.git_exported_at,
            "message": "Версии синхронизированы.",
        })


# ==================== Legacy Aliases ====================


def cmd_export_script(args):
    """Legacy alias for checkout (script)."""
    args.component_type = "script"
    args.id = args.script_id
    args.name = args.script_name
    cmd_checkout(args)


def cmd_import_script(args):
    """Legacy alias for publish (script)."""
    cmd_publish(args)


def cmd_export_datasource_type(args):
    """Legacy alias for checkout (datasource_type)."""
    args.component_type = "datasource_type"
    args.id = args.type_id
    args.name = args.type_name
    cmd_checkout(args)


def cmd_export_activator_type(args):
    """Legacy alias for checkout (activator_type)."""
    args.component_type = "activator_type"
    args.id = args.type_id
    args.name = args.type_name
    cmd_checkout(args)


# ==================== Main ====================


def main():
    parser = argparse.ArgumentParser(
        description="GIMS Local-First Workflow CLI - checkout/publish automation components",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Checkout script to local directory
  python gims_sync.py checkout --component-type script --name "ICMP Monitor" --output-dir ./scripts/icmp_monitor/

  # Checkout all scripts from a folder
  python gims_sync.py checkout-folder --component-type script --folder-name "Мониторинг" --output-base-dir ./scripts/

  # Publish local changes (two-stage: preview first)
  python gims_sync.py publish --input-dir ./scripts/icmp_monitor/
  python gims_sync.py publish --input-dir ./scripts/icmp_monitor/ --confirm

  # Check status of local components vs GIMS
  python gims_sync.py status --base-dir ./scripts/

  # Find duplicates before creating
  python gims_sync.py find-duplicates --name "ICMP Monitor" --component-type script

  # Validate Python code
  python gims_sync.py validate-code --file ./scripts/icmp_monitor/code.py
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ==================== checkout ====================
    checkout_parser = subparsers.add_parser("checkout", help="Checkout component from GIMS to local files")
    checkout_parser.add_argument("--component-type", required=True, choices=["script", "datasource_type", "activator_type"])
    checkout_parser.add_argument("--id", type=int, help="Component ID in GIMS")
    checkout_parser.add_argument("--name", help="Component name in GIMS")
    checkout_parser.add_argument("--output-dir", help="Output directory (default: component_name)")
    checkout_parser.add_argument("--dry-run", action="store_true", help="Show what would be checked out")
    checkout_parser.add_argument("--force", action="store_true", help="Overwrite local files even if modified")

    # ==================== checkout-folder ====================
    checkout_folder_parser = subparsers.add_parser("checkout-folder", help="Checkout all components from a GIMS folder")
    checkout_folder_parser.add_argument("--component-type", required=True, choices=["script", "datasource_type", "activator_type"])
    checkout_folder_parser.add_argument("--folder-id", type=int, help="Folder ID in GIMS")
    checkout_folder_parser.add_argument("--folder-name", help="Folder name in GIMS")
    checkout_folder_parser.add_argument("--output-base-dir", help="Base output directory (default: current dir)")
    checkout_folder_parser.add_argument("--dry-run", action="store_true", help="Show what would be checked out")
    checkout_folder_parser.add_argument("--force", action="store_true", help="Overwrite local files even if modified")

    # ==================== publish ====================
    publish_parser = subparsers.add_parser("publish", help="Publish local files to GIMS (two-stage)")
    publish_parser.add_argument("--input-dir", required=True, help="Input directory with meta.yaml and code")
    publish_parser.add_argument("--target-name", help="Override component name")
    publish_parser.add_argument("--folder-id", type=int, help="Target folder ID in GIMS")
    publish_parser.add_argument("--confirm", action="store_true", help="Confirm and execute publish (stage 2)")
    publish_parser.add_argument("--force", action="store_true", help="Force publish even if GIMS is newer")

    # ==================== publish-all ====================
    publish_all_parser = subparsers.add_parser("publish-all", help="Publish all modified components from a directory")
    publish_all_parser.add_argument("--base-dir", required=True, help="Base directory with component subdirectories")
    publish_all_parser.add_argument("--dry-run", action="store_true", help="Show what would be published")
    publish_all_parser.add_argument("--confirm", action="store_true", help="Confirm and execute publish")
    publish_all_parser.add_argument("--force", action="store_true", help="Continue on errors")

    # ==================== status ====================
    status_parser = subparsers.add_parser("status", help="Show status of local components vs GIMS")
    status_parser.add_argument("--base-dir", required=True, help="Base directory with component subdirectories")

    # ==================== find-duplicates ====================
    duplicates_parser = subparsers.add_parser("find-duplicates", help="Find components with similar names")
    duplicates_parser.add_argument("--name", required=True, help="Name to search for")
    duplicates_parser.add_argument("--component-type", required=True, choices=["script", "datasource_type", "activator_type"])
    duplicates_parser.add_argument("--threshold", type=float, default=0.6, help="Similarity threshold (0-1, default: 0.6)")

    # ==================== validate-code ====================
    validate_parser = subparsers.add_parser("validate-code", help="Validate Python code syntax")
    validate_parser.add_argument("--file", help="Python file to validate")
    validate_parser.add_argument("--code", help="Python code string to validate")

    # ==================== compare ====================
    compare_parser = subparsers.add_parser("compare", help="Compare GIMS component with Git version")
    compare_parser.add_argument("--component-type", required=True, choices=["script", "datasource_type", "activator_type"])
    compare_parser.add_argument("--gims-name", required=True, help="Component name in GIMS")
    compare_parser.add_argument("--git-exported-at", required=True, help="Export date from Git meta.yaml (ISO format)")

    # ==================== Legacy commands (aliases) ====================
    export_script = subparsers.add_parser("export-script", help="[Legacy] Export script to Git format")
    export_script.add_argument("--script-id", type=int, help="Script ID")
    export_script.add_argument("--script-name", help="Script name")
    export_script.add_argument("--output-dir", help="Output directory (default: script_name)")
    export_script.add_argument("--dry-run", action="store_true", help="Show what would be exported")
    export_script.add_argument("--force", action="store_true", help="Overwrite local files")

    import_script = subparsers.add_parser("import-script", help="[Legacy] Import script from Git format")
    import_script.add_argument("--input-dir", required=True, help="Input directory with meta.yaml and code.py")
    import_script.add_argument("--target-name", help="Override script name")
    import_script.add_argument("--folder-id", type=int, help="Target folder ID")
    import_script.add_argument("--update-existing", action="store_true", help="[Deprecated] Use --confirm instead")
    import_script.add_argument("--dry-run", action="store_true", help="Show what would be imported")
    import_script.add_argument("--confirm", action="store_true", help="Confirm and execute")

    export_ds = subparsers.add_parser("export-datasource-type", help="[Legacy] Export datasource type to Git format")
    export_ds.add_argument("--type-id", type=int, help="Type ID")
    export_ds.add_argument("--type-name", help="Type name")
    export_ds.add_argument("--output-dir", help="Output directory (default: type_name)")
    export_ds.add_argument("--dry-run", action="store_true", help="Show what would be exported")
    export_ds.add_argument("--force", action="store_true", help="Overwrite local files")

    export_act = subparsers.add_parser("export-activator-type", help="[Legacy] Export activator type to Git format")
    export_act.add_argument("--type-id", type=int, help="Type ID")
    export_act.add_argument("--type-name", help="Type name")
    export_act.add_argument("--output-dir", help="Output directory (default: type_name)")
    export_act.add_argument("--dry-run", action="store_true", help="Show what would be exported")
    export_act.add_argument("--force", action="store_true", help="Overwrite local files")

    args = parser.parse_args()

    try:
        handlers = {
            "checkout": cmd_checkout,
            "checkout-folder": cmd_checkout_folder,
            "publish": cmd_publish,
            "publish-all": cmd_publish_all,
            "status": cmd_status,
            "find-duplicates": cmd_find_duplicates,
            "validate-code": cmd_validate_code,
            "compare": cmd_compare,
            # Legacy aliases
            "export-script": cmd_export_script,
            "import-script": cmd_import_script,
            "export-datasource-type": cmd_export_datasource_type,
            "export-activator-type": cmd_export_activator_type,
        }
        handlers[args.command](args)
    except GimsApiError as e:
        print_json({
            "status": "error",
            "message": e.message,
            "detail": e.detail,
        })
        sys.exit(1)
    except Exception as e:
        print_json({
            "status": "error",
            "message": str(e),
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
