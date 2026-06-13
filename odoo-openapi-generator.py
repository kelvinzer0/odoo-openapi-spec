#!/usr/bin/env python3
"""
Odoo → OpenAPI 3.1.0 Generator
Introspects all models from an Odoo instance and generates a full OpenAPI spec.
"""

import xmlrpc.client
import json
import sys
from collections import defaultdict

# ─── Config (from environment variables) ──────────────────────────────
import os
URL = os.environ.get("ODOO_URL", "http://localhost:8069")
DB = os.environ.get("ODOO_DB", "odoo")
USER = os.environ.get("ODOO_USER", "admin")
PASS = os.environ.get("ODOO_PASS", "admin")

# Models to skip (internal / abstract / transient)
SKIP_PREFIXES = (
    'ir.', 'base.', 'report.', 'bus.',
    'web_editor.', 'web_tour.', 'http_routing.',
)
SKIP_MODELS = {
    'base_language_install', 'base_import_module',
    'base_module_update', 'base_module_upgrade',
    'base_module_uninstall', 'base_partner_merge',
    'change_password_wizard', 'change_password_user',
}

# Field type → OpenAPI type mapping
FIELD_TYPE_MAP = {
    'char': {'type': 'string'},
    'text': {'type': 'string'},
    'html': {'type': 'string', 'format': 'html'},
    'integer': {'type': 'integer'},
    'float': {'type': 'number', 'format': 'double'},
    'monetary': {'type': 'number', 'format': 'double'},
    'boolean': {'type': 'boolean'},
    'date': {'type': 'string', 'format': 'date'},
    'datetime': {'type': 'string', 'format': 'date-time'},
    'binary': {'type': 'string', 'format': 'byte'},
    'selection': {'type': 'string'},
    'json': {'type': 'object'},
    'reference': {'type': 'string'},
}

# ─── Connect ──────────────────────────────────────────────────────────
print("Connecting to Odoo...", file=sys.stderr)
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
version = common.version()
uid = common.authenticate(DB, USER, PASS, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

print(f"Connected: Odoo {version['server_version']} | UID: {uid}", file=sys.stderr)


def rpc(model, method, args=None, kwargs=None):
    """Call Odoo XML-RPC."""
    return models.execute_kw(DB, uid, PASS, model, method, args or [], kwargs or {})


# ─── Introspect Models ────────────────────────────────────────────────
print("Fetching model list...", file=sys.stderr)
all_models = rpc('ir.model', 'search_read', [[['state', '!=', 'manual']]], {
    'fields': ['model', 'name', 'info'],
})

# Filter
model_list = []
for m in all_models:
    name = m['model']
    if name in SKIP_MODELS:
        continue
    if any(name.startswith(p) for p in SKIP_PREFIXES):
        continue
    model_list.append({'model': name, 'name': m['name'] or name, 'info': m.get('info', '')})

model_list.sort(key=lambda x: x['model'])
print(f"Found {len(model_list)} models to process", file=sys.stderr)

# ─── Fetch Fields ─────────────────────────────────────────────────────
print("Fetching fields for all models...", file=sys.stderr)
model_fields = {}

# Batch fetch all fields at once
all_fields = rpc('ir.model.fields', 'search_read', [[]], {
    'fields': ['model', 'name', 'field_description', 'ttype', 'required', 'readonly', 'relation', 'selection'],
})

fields_by_model = defaultdict(list)
for f in all_fields:
    fields_by_model[f['model']].append(f)

# ─── Build OpenAPI ────────────────────────────────────────────────────
print("Building OpenAPI spec...", file=sys.stderr)

paths = {}
schemas = {}

# Odoo domain filter schema
domain_schema = {
    "type": "array",
    "items": {
        "type": "array",
        "prefixItems": [
            {"type": "string", "description": "Field name"},
            {"type": "string", "enum": ["=", "!=", ">", "<", ">=", "<=", "like", "ilike", "in", "not in", "child_of", "parent_of"]},
        ],
        "description": "Domain filter tuple [field, operator, value]",
    },
    "description": "Odoo domain filter, e.g. [[\"name\", \"ilike\", \"test\"]]",
}

for m in model_list:
    model_name = m['model']
    friendly_name = m['name']
    tag = model_name.split('.')[0]  # group tag

    # Get fields for this model
    flds = fields_by_model.get(model_name, [])
    if not flds:
        continue

    # Build schema for this model
    properties = {}
    required_fields = []

    for f in flds:
        fname = f['name']
        ftype = f['ttype']
        fdesc = f['field_description'] or fname

        if ftype in ('one2many',):
            # Read-only list of IDs
            properties[fname] = {
                "type": "array",
                "items": {"type": "integer"},
                "description": f"{fdesc} (One2many → list of IDs)",
                "readOnly": True,
            }
        elif ftype == 'many2many':
            properties[fname] = {
                "type": "array",
                "items": {"type": "integer"},
                "description": f"{fdesc} (Many2many → list of IDs)",
            }
        elif ftype == 'many2one':
            properties[fname] = {
                "oneOf": [
                    {"type": "integer", "description": f"ID of related {f.get('relation', 'record')}"},
                    {
                        "type": "array",
                        "items": {},
                        "description": "[id, display_name]",
                        "maxItems": 2,
                        "minItems": 2,
                    },
                ],
                "description": f"{fdesc} (Many2one → ID or [id, name])",
            }
        else:
            schema = FIELD_TYPE_MAP.get(ftype, {'type': 'string'}).copy()
            schema['description'] = fdesc
            if ftype == 'selection' and f.get('selection'):
                try:
                    sel = json.loads(f['selection']) if isinstance(f['selection'], str) else f['selection']
                    if isinstance(sel, list) and sel:
                        schema['enum'] = [s[0] for s in sel if isinstance(s, (list, tuple)) and len(s) >= 2]
                except Exception:
                    pass
            properties[fname] = schema

        if f.get('required') and fname not in ('id', 'display_name', 'create_date', 'write_date', 'create_uid', 'write_uid'):
            required_fields.append(fname)

    # Schema name
    schema_name = model_name.replace('.', '_')

    schemas[schema_name] = {
        "type": "object",
        "properties": properties,
    }
    if required_fields:
        schemas[schema_name]["required"] = required_fields

    # Create/Write schema (exclude read-only fields)
    create_props = {}
    for fname, fdef in properties.items():
        if fname in ('id', 'display_name', 'create_date', 'write_date', 'create_uid', 'write_uid', '__last_update'):
            continue
        if fdef.get('readOnly'):
            continue
        create_props[fname] = {k: v for k, v in fdef.items() if k != 'readOnly'}

    create_schema_name = f"{schema_name}_create"
    schemas[create_schema_name] = {
        "type": "object",
        "properties": create_props,
    }
    if required_fields:
        schemas[create_schema_name]["required"] = [f for f in required_fields if f in create_props]

    update_schema_name = f"{schema_name}_update"
    schemas[update_schema_name] = {
        "type": "object",
        "properties": create_props,
        "description": "Fields to update (partial update supported)",
    }

    # ─── Paths ────────────────────────────────────────────────────
    base_path = f"/xmlrpc/2/{model_name}"

    # POST /search_read — list/search
    paths[f"/api/{model_name}"] = {
        "get": {
            "summary": f"Search & read {friendly_name}",
            "description": f"Search and read {model_name} records. Uses Odoo `search_read` method.",
            "operationId": f"search_{schema_name}",
            "tags": [tag],
            "parameters": [
                {
                    "name": "domain",
                    "in": "query",
                    "description": "JSON-encoded Odoo domain filter",
                    "schema": {"type": "string"},
                    "example": '[["name","ilike","test"]]',
                },
                {
                    "name": "fields",
                    "in": "query",
                    "description": "Comma-separated field names to return",
                    "schema": {"type": "string"},
                    "example": "name,default_code,list_price",
                },
                {
                    "name": "limit",
                    "in": "query",
                    "schema": {"type": "integer", "default": 80},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "schema": {"type": "integer", "default": 0},
                },
                {
                    "name": "order",
                    "in": "query",
                    "description": "Sort order, e.g. 'name asc' or 'create_date desc'",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": f"List of {friendly_name} records",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{schema_name}"},
                            }
                        }
                    },
                },
            },
            "x-odoo-method": "search_read",
            "x-odoo-model": model_name,
        },
        "post": {
            "summary": f"Create {friendly_name}",
            "description": f"Create a new {model_name} record. Uses Odoo `create` method.",
            "operationId": f"create_{schema_name}",
            "tags": [tag],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{create_schema_name}"},
                    }
                },
            },
            "responses": {
                "201": {
                    "description": "Created record ID",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer", "description": "ID of created record"},
                                },
                            }
                        }
                    },
                },
            },
            "x-odoo-method": "create",
            "x-odoo-model": model_name,
        },
    }

    # GET/PUT/DELETE by ID
    paths[f"/api/{model_name}/{{id}}"] = {
        "get": {
            "summary": f"Get {friendly_name} by ID",
            "description": f"Read a single {model_name} record by ID. Uses Odoo `read` method.",
            "operationId": f"get_{schema_name}",
            "tags": [tag],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "Record ID",
                },
                {
                    "name": "fields",
                    "in": "query",
                    "description": "Comma-separated field names to return",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": f"{friendly_name} record",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{schema_name}"},
                        }
                    },
                },
                "404": {"description": "Record not found"},
            },
            "x-odoo-method": "read",
            "x-odoo-model": model_name,
        },
        "put": {
            "summary": f"Update {friendly_name}",
            "description": f"Update an existing {model_name} record. Uses Odoo `write` method.",
            "operationId": f"update_{schema_name}",
            "tags": [tag],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "Record ID to update",
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{update_schema_name}"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Update successful",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "id": {"type": "integer"},
                                },
                            }
                        }
                    },
                },
            },
            "x-odoo-method": "write",
            "x-odoo-model": model_name,
        },
        "delete": {
            "summary": f"Delete {friendly_name}",
            "description": f"Delete a {model_name} record. Uses Odoo `unlink` method.",
            "operationId": f"delete_{schema_name}",
            "tags": [tag],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "Record ID to delete",
                },
            ],
            "responses": {
                "200": {
                    "description": "Delete successful",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                    "id": {"type": "integer"},
                                },
                            }
                        }
                    },
                },
            },
            "x-odoo-method": "unlink",
            "x-odoo-model": model_name,
        },
    }

    # POST /api/{model}/{id}/call — call any method
    paths[f"/api/{model_name}/{{id}}/call"] = {
        "post": {
            "summary": f"Call method on {friendly_name}",
            "description": f"Call any method on a {model_name} record. Uses Odoo `execute_kw` with method name.",
            "operationId": f"call_{schema_name}",
            "tags": [tag],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string", "description": "Method name to call", "example": "action_confirm"},
                                "args": {"type": "array", "items": {}, "description": "Positional arguments"},
                                "kwargs": {"type": "object", "description": "Keyword arguments"},
                            },
                            "required": ["method"],
                        }
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Method call result",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "result": {},
                                },
                            }
                        }
                    },
                },
            },
            "x-odoo-method": "execute_kw",
            "x-odoo-model": model_name,
        },
    }

# ─── Assemble Spec ────────────────────────────────────────────────────
# Sort tags
tags = sorted(set(t for path_ops in paths.values() for op in path_ops.values() for t in op.get('tags', [])))
tag_objects = [{"name": t, "description": f"Operations on {t}.* models"} for t in tags]

spec = {
    "openapi": "3.1.0",
    "info": {
        "title": "Odoo Warung Lakku — Full API",
        "description": (
            "Auto-generated OpenAPI specification from Odoo instance.\n\n"
            f"**Odoo Version:** {version['server_version']}\n"
            f"**Database:** {DB}\n"
            f"**Models:** {len(model_list)} models\n\n"
            "## How to use\n\n"
            "This spec describes the Odoo XML-RPC API in OpenAPI format.\n"
            "All endpoints map to Odoo's XML-RPC `execute_kw` calls.\n\n"
            "### Authentication\n"
            "Use Odoo XML-RPC authentication:\n"
            "1. Call `/xmlrpc/2/common` → `authenticate(db, login, password, {})` to get UID\n"
            "2. Use UID + password for all subsequent calls\n\n"
            "### x-odoo-method / x-odoo-model\n"
            "Each operation has `x-odoo-method` and `x-odoo-model` extensions\n"
            "that describe the exact Odoo RPC call to make.\n\n"
            "### Supported Operations\n"
            "- **GET /api/{model}** → `search_read(domain, fields, limit, offset, order)`\n"
            "- **POST /api/{model}** → `create(vals)`\n"
            "- **GET /api/{model}/{id}** → `read([id], fields)`\n"
            "- **PUT /api/{model}/{id}** → `write([id], vals)`\n"
            "- **DELETE /api/{model}/{id}** → `unlink([id])`\n"
            "- **POST /api/{model}/{id}/call** → `execute_kw(model, method, [id], args, kwargs)`\n"
        ),
        "version": version['server_version'],
        "contact": {
            "name": "Warung Lakku",
            "url": URL,
        },
    },
    "servers": [
        {
            "url": URL,
            "description": "Odoo Instance",
        }
    ],
    "tags": tag_objects,
    "paths": paths,
    "components": {
        "schemas": schemas,
        "securitySchemes": {
            "odoo_auth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Odoo UID:password or API key. First authenticate via XML-RPC to get UID.",
            },
            "odoo_xmlrpc": {
                "type": "http",
                "scheme": "basic",
                "description": "Use Odoo XML-RPC authenticate() to get UID, then use UID:password for calls.",
            },
        },
    },
    "security": [{"odoo_xmlrpc": []}],
}

# ─── Output ───────────────────────────────────────────────────────────
output = json.dumps(spec, indent=2, ensure_ascii=False)
print(output)

print(f"\nDone! Generated spec with {len(paths)} paths and {len(schemas)} schemas.", file=sys.stderr)
