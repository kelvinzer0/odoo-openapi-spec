import json, copy

with open('odoo-openapi-compact.json', 'r') as f:
    spec = json.load(f)

# First: restore from backup to get fresh _create + _update schemas
with open('odoo-openapi-compact.json.bak', 'r') as f:
    spec = json.load(f)

# Define unique key fields per model (verified against live Odoo instance)
MODEL_KEYS = {
    'account.account':         {'key': ['code'], 'desc': 'Account Code (unique per company)'},
    'account.journal':         {'key': ['code'], 'desc': 'Journal Code (unique per company)'},
    'account.move':            {'key': ['name'], 'desc': 'Entry Number'},
    'account.move.line':       {'key': ['name'], 'desc': 'Line Description'},
    'account.payment':         {'key': ['name'], 'desc': 'Payment Number'},
    'account.tax':             {'key': ['name'], 'desc': 'Tax Name'},
    'account.tax.group':       {'key': ['name'], 'desc': 'Tax Group Name'},
    'crm.lead':                {'key': ['name'], 'desc': 'Opportunity Name'},
    'crm.stage':               {'key': ['name'], 'desc': 'Stage Name'},
    'crm.tag':                 {'key': ['name'], 'desc': 'Tag Name'},
    'hr.department':           {'key': ['name'], 'desc': 'Department Name'},
    'hr.employee':             {'key': ['work_email'], 'desc': 'Work Email'},
    'hr.job':                  {'key': ['name'], 'desc': 'Job Position Name'},
    'mail.message':            {'key': ['subject'], 'desc': 'Message Subject'},
    'mail.thread':             {'key': ['id'], 'desc': 'Thread ID'},
    'mrp.bom':                 {'key': ['code'], 'desc': 'BoM Reference'},
    'mrp.production':          {'key': ['name'], 'desc': 'Production Number'},
    'mrp.workorder':           {'key': ['name'], 'desc': 'Work Order Name'},
    'pos.config':              {'key': ['name'], 'desc': 'POS Config Name'},
    'pos.order':               {'key': ['name'], 'desc': 'Order Reference'},
    'pos.order.line':          {'key': ['name'], 'desc': 'Order Line Reference'},
    'pos.session':             {'key': ['name'], 'desc': 'Session Name'},
    'product.attribute':       {'key': ['name'], 'desc': 'Attribute Name'},
    'product.attribute.value': {'key': ['name'], 'desc': 'Attribute Value Name'},
    'product.category':        {'key': ['name'], 'desc': 'Category Name'},
    'product.product':         {'key': ['barcode'], 'desc': 'Barcode (unique)'},
    'product.template':        {'key': ['name'], 'desc': 'Product Name'},
    'project.project':         {'key': ['name'], 'desc': 'Project Name'},
    'project.task':            {'key': ['name'], 'desc': 'Task Title'},
    'purchase.order':          {'key': ['name'], 'desc': 'PO Number'},
    'purchase.order.line':     {'key': ['name'], 'desc': 'PO Line Description'},
    'res.partner':             {'key': ['email'], 'desc': 'Email Address'},
    'res.partner.bank':        {'key': ['acc_number'], 'desc': 'Bank Account Number'},
    'res.partner.category':    {'key': ['name'], 'desc': 'Partner Tag Name'},
    'sale.order':              {'key': ['name'], 'desc': 'SO Number'},
    'sale.order.line':         {'key': ['name'], 'desc': 'SO Line Description'},
    'stock.location':          {'key': ['complete_name'], 'desc': 'Full Location Path'},
    'stock.move':              {'key': ['name'], 'desc': 'Move Reference'},
    'stock.move.line':         {'key': ['name'], 'desc': 'Move Line Description'},
    'stock.picking':           {'key': ['name'], 'desc': 'Picking Reference'},
    'stock.picking.type':      {'key': ['name'], 'desc': 'Picking Type Name'},
    'stock.quant':             {'key': ['id'], 'desc': 'Quant ID'},
    'stock.warehouse':         {'key': ['name'], 'desc': 'Warehouse Name'},
    'uom.category':            {'key': ['name'], 'desc': 'UoM Category Name'},
    'uom.uom':                 {'key': ['name'], 'desc': 'UoM Name'},
}

paths = spec['paths']
schemas = spec['components']['schemas']

# ── Step 1: Find models with POST + PUT pair ──
models_to_upsert = []
for path, methods in list(paths.items()):
    if path.endswith('/call'):
        continue
    if '/{id}' in path:
        if 'put' in methods:
            base_path = path.replace('/{id}', '')
            if base_path in paths and 'post' in paths[base_path]:
                model = methods['put'].get('x-odoo-model', '')
                if model and model in MODEL_KEYS:
                    models_to_upsert.append({
                        'collection_path': base_path,
                        'item_path': path,
                        'model': model,
                    })

print(f"Found {len(models_to_upsert)} models to upsert")

# ── Step 2: Build upsert schemas ──
for m in models_to_upsert:
    model = m['model']
    schema_name = model.replace('.', '_')
    key_info = MODEL_KEYS[model]

    create_key = f"{schema_name}_create"
    update_key = f"{schema_name}_update"
    upsert_key = f"{schema_name}_upsert"

    create_schema = schemas.get(create_key, {})
    update_schema = schemas.get(update_key, {})

    if not create_schema:
        print(f"  SKIP {model}: no create schema")
        continue

    # Build upsert schema:
    # 1. _key object (required) - search criteria
    # 2. All fields from create schema (merged with update)
    # 3. No 'required' on data fields (partial updates supported)
    upsert_props = {}

    # _key: the search fields
    key_props = {}
    for kf in key_info['key']:
        # Copy field definition from create schema if available
        if kf in create_schema.get('properties', {}):
            key_props[kf] = copy.deepcopy(create_schema['properties'][kf])
        elif kf in update_schema.get('properties', {}):
            key_props[kf] = copy.deepcopy(update_schema['properties'][kf])
        else:
            key_props[kf] = {"type": "string"}

    upsert_props['_key'] = {
        "type": "object",
        "description": f"Search criteria to find existing record by {key_info['desc']}",
        "properties": key_props,
        "required": list(key_info['key']),
    }

    # Data fields: all from create + any extras from update
    all_props = dict(create_schema.get('properties', {}))
    for k, v in update_schema.get('properties', {}).items():
        if k not in all_props:
            all_props[k] = v

    upsert_props.update(all_props)

    upsert_schema = {
        "type": "object",
        "description": f"Upsert {model} record. Use _key to search, data fields to create/update.",
        "properties": upsert_props,
        "required": ["_key"],
    }

    schemas[upsert_key] = upsert_schema

    # Remove old schemas
    if create_key in schemas:
        del schemas[create_key]
    if update_key in schemas:
        del schemas[update_key]

    print(f"  SCHEMA: {create_key} + {update_key} → {upsert_key}")

# ── Step 3: Transform paths ──
for m in models_to_upsert:
    collection_path = m['collection_path']
    item_path = m['item_path']
    model = m['model']
    schema_name = model.replace('.', '_')
    upsert_key = f"{schema_name}_upsert"
    key_info = MODEL_KEYS[model]

    # Build upsert PUT operation
    upsert_op = copy.deepcopy(paths[collection_path]['post'])

    model_title = model.split('.')[-1].replace('_', ' ').title()
    key_desc = f"by {', '.join(key_info['key'])} ({key_info['desc']})"

    upsert_op['summary'] = f"Upsert {model_title}"
    upsert_op['description'] = (
        f"Create or update {model} record.\n\n"
        f"Search {key_desc} from `_key`. "
        f"If found → update with data fields, if not → create new record."
    )
    upsert_op['operationId'] = f"upsert_{schema_name}"
    upsert_op['requestBody'] = {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "$ref": f"#/components/schemas/{upsert_key}"
                }
            }
        }
    }
    upsert_op['responses'] = {
        "200": {
            "description": "Upsert result",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "ID of created or updated record"
                            },
                            "created": {
                                "type": "boolean",
                                "description": "true if created, false if updated"
                            },
                            "matched_by": {
                                "type": "string",
                                "description": f"The key field value that matched (e.g. {', '.join(key_info['key'])})"
                            }
                        }
                    }
                }
            }
        }
    }
    upsert_op['x-odoo-method'] = 'create_or_write'
    upsert_op['x-odoo-model'] = model

    # Remove POST from collection
    if 'post' in paths[collection_path]:
        del paths[collection_path]['post']

    # Add PUT upsert to collection
    paths[collection_path]['put'] = upsert_op

    # Remove PUT from item path
    if item_path in paths and 'put' in paths[item_path]:
        del paths[item_path]['put']

    print(f"  PATH: {collection_path} → PUT upsert ({', '.join(key_info['key'])})")

# ── Step 4: Write output ──
with open('odoo-openapi-compact.json', 'w') as f:
    json.dump(spec, f, indent=2)

# ── Summary ──
remaining_posts = sum(1 for p, m in paths.items() if 'post' in m and not p.endswith('/call'))
remaining_puts = sum(1 for p, m in paths.items() if 'put' in m)
total_upserts = sum(1 for s in schemas if s.endswith('_upsert'))

print(f"\n=== DONE ===")
print(f"Upsert schemas: {total_upserts}")
print(f"Remaining POST: {remaining_posts}")
print(f"Remaining PUT: {remaining_puts}")
