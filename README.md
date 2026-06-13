# Odoo OpenAPI Spec

Auto-generated OpenAPI 3.1.0 specification from Odoo 17.0 instance.

## Files

| File | Size | Description |
|---|---|---|
| `odoo-openapi.json` | ~11 MB | Full spec — all 494 models |
| `odoo-openapi-compact.json` | ~2.3 MB | Business models only (135 paths) |
| `odoo-openapi-generator.py` | — | Generator script (reusable) |
| `odoo_rest_api/` | — | Odoo module — REST API controller |
| `server.py` | — | FastAPI proxy (standalone alternative) |

## Models Included (Compact)

Product, Partner, Sale, Purchase, Account/Invoice, Stock, CRM, POS, HR, MRP, Project, UoM

## Endpoint Pattern

| Method | Path | Description | Odoo Method |
|---|---|---|---|
| `GET` | `/api/{model}` | Search & read records | `search_read()` |
| `GET` | `/api/{model}/{id}` | Read single record | `read()` |
| `PUT` | `/api/{model}` | **Upsert** (create/update by unique key) | `search()` → `create()` or `write()` |
| `PUT` | `/api/{model}/{id}` | Update by ID | `write()` |
| `DELETE` | `/api/{model}/{id}` | Delete record | `unlink()` |

### Upsert

Use `_key` to search existing record. If found → update, if not → create.

```json
PUT /api/res.partner
{
  "_key": { "email": "john@example.com" },
  "name": "John Doe",
  "phone": "+6281234"
}
```

### Unique Key per Model

| Model | Key Field |
|---|---|
| `account.account` | `code` |
| `res.partner` | `email` |
| `product.product` | `barcode` |
| `product.template` | `name` |
| `sale.order` | `name` |
| `purchase.order` | `name` |
| `stock.picking` | `name` |
| `hr.employee` | `work_email` |
| `uom.uom` | `name` |

See `MODEL_KEYS` in source for full list.

## Install as Odoo Module

### Prerequisites

- Odoo 17.0 running instance
- Access to addons path

### Steps

1. Copy `odoo_rest_api/` folder to your Odoo addons path:

```bash
cp -r odoo_rest_api /path/to/odoo/addons/
```

Or add the repo directory to your Odoo config:

```ini
[options]
addons_path = /path/to/odoo/addons,/path/to/odoo-openapi-spec
```

2. Restart Odoo server:

```bash
systemctl restart odoo
# or
./odoo-bin -c odoo.conf
```

3. Activate **Developer Mode**:
   - Go to `Settings` → scroll to bottom → click **Activate the developer mode**

4. Install the module:
   - Go to `Apps` → click **Update Apps List** (menu icon)
   - Search for **"REST API"**
   - Click **Install**

5. Test the API:

```bash
# Search partners
curl -u "email:password" \
  "http://localhost:8069/api/res.partner?limit=3&fields=name,email"

# Upsert partner
curl -u "email:password" \
  -X PUT "http://localhost:8069/api/res.partner" \
  -H "Content-Type: application/json" \
  -d '{"_key":{"email":"test@example.com"},"name":"Test Partner"}'

# Read by ID
curl -u "email:password" \
  "http://localhost:8069/api/res.partner/1"

# Delete
curl -u "email:password" \
  -X DELETE "http://localhost:8069/api/res.partner/1"
```

### Authentication

HTTP Basic Auth using Odoo email + password:

```
Authorization: Basic base64(email:password)
```

## Standalone FastAPI Proxy (Alternative)

If you don't want to install the Odoo module, use the FastAPI proxy:

```bash
pip install fastapi uvicorn httpx
python3 server.py
```

Then open Swagger UI at `http://localhost:8000/docs`.

The proxy translates REST calls to Odoo XML-RPC automatically.

## Regenerate Spec

```bash
python3 odoo-openapi-generator.py > odoo-openapi.json
```

Edit the config in the script (URL, DB, USER, PASS) to point to your Odoo instance.

## Odoo Version

```
Server: 17.0
```
