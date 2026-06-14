# Odoo REST API

OpenAPI 3.1.0 spec + REST API module for Odoo 17. Expose any Odoo model as REST endpoints with Bearer token authentication.

## Features

- **REST API** for all Odoo models (45 business models)
- **Bearer Token** authentication (generate from UI, no password needed)
- **Upsert** support (create or update by unique key)
- **API Console** with Scalar UI for interactive documentation
- **OpenAPI 3.1.0** spec served at `/api/spec`

## Installation

### Prerequisites

- Odoo 17.0 running instance (Docker or bare metal)
- Access to addons path

### Steps

1. Copy `odoo_rest_api/` to your Odoo addons path:

```bash
cp -r odoo_rest_api /path/to/odoo/addons/
```

Or add the module directory to your Odoo config:

```ini
[options]
addons_path = /path/to/odoo/addons,/path/to/odoo-openapi-spec
```

2. Restart Odoo:

```bash
docker restart odoo
# or
systemctl restart odoo
```

3. Activate **Developer Mode**: Settings → Activate the developer mode

4. Install module: Apps → Update Apps List → Search "REST API" → Install

5. Open **REST API → API Console** in the Odoo menu

## Authentication

### Bearer Token (Recommended)

1. Go to **REST API → API Console** in Odoo backend
2. Click **Generate Token**
3. Copy the token

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8069/api/res.partner?limit=3&fields=name,email"
```

### Basic Auth

```bash
curl -u "email:password" \
  "http://localhost:8069/api/res.partner?limit=3&fields=name,email"
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/{model}` | Search & read records |
| `GET` | `/api/{model}/{id}` | Read single record |
| `PUT` | `/api/{model}` | Upsert (create/update by unique key) |
| `PUT` | `/api/{model}/{id}` | Update by ID |
| `DELETE` | `/api/{model}/{id}` | Delete record |

### Query Parameters (GET)

| Param | Example | Description |
|---|---|---|
| `fields` | `name,email,phone` | Comma-separated field list |
| `limit` | `10` | Max records (default 20) |
| `offset` | `0` | Pagination offset |
| `order` | `name asc` | Sort order |
| `domain` | `[["active","=",true]]` | Odoo domain filter (JSON) |

### Upsert

Use `_key` to find existing record. If found → update, if not → create.

```bash
curl -H "Authorization: Bearer <token>" \
  -X PUT "http://localhost:8069/api/res.partner" \
  -H "Content-Type: application/json" \
  -d '{
    "_key": { "email": "john@example.com" },
    "name": "John Doe",
    "phone": "+6281234"
  }'
```

### Unique Keys

| Model | Key |
|---|---|
| `account.account` | `code` |
| `account.journal` | `code` |
| `crm.lead` | `name` |
| `hr.employee` | `work_email` |
| `product.product` | `barcode` |
| `product.template` | `name` |
| `purchase.order` | `name` |
| `res.partner` | `email` |
| `sale.order` | `name` |
| `stock.picking` | `name` |

See `MODEL_KEYS` in `controllers/main.py` for full list.

## Supported Models

Account, Journal, Move, Payment, Tax, CRM (Lead, Stage, Tag), HR (Department, Employee, Job), MRP (BOM, Production, Workorder), POS (Config, Order, Session), Product (Attribute, Category, Product, Template), Project, Purchase, Partner, Sale, Stock (Location, Move, Picking, Quant, Warehouse), UoM

## API Reference

- **Scalar UI**: `http://localhost:8069/api/spec/docs`
- **Full spec**: `http://localhost:8069/api/spec` (469 paths, all Odoo models)
- **Compact spec**: `http://localhost:8069/api/spec/compact` (45 paths, business models)

## n8n Automation

Connect to [n8n](https://n8n.io) for workflow automation:

```bash
# Install Odoo node in n8n
npm install @n8n-dev/n8n-nodes-odoo-v17
```

Configure in n8n:
- **Base URL:** `http://localhost:8069`
- **Authentication:** Bearer Token (generate from API Console)

Example workflows:
- Shopify orders → Odoo Sale Orders
- CRM lead won → Auto-create Invoice
- Daily stock report → Slack notification
- New HR employee → Create Odoo user

## File Structure

```
odoo_rest_api/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py          # REST API controller + auth
├── static/spec/
│   ├── odoo-openapi.json        # Full OpenAPI spec
│   └── odoo-openapi-compact.json # Compact spec
└── views/
    ├── credentials_template.xml # API Console UI
    └── menu.xml                 # Odoo menu items
```

## Odoo Version

```
Server: 17.0
OpenAPI: 3.1.0
```
