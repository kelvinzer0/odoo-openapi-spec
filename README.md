# REST API for Odoo

Expose any Odoo model as REST API endpoints with Bearer token authentication, upsert support, and interactive API documentation.

## Features

- **REST API** for 45 business models (Account, CRM, HR, POS, Product, Sale, Stock, etc.)
- **Bearer Token** authentication — generate from Odoo UI, no password needed
- **Upsert** — create or update records by unique key in one call
- **Smart Relational Fields** — send category name instead of ID, auto-resolves
- **API Console** — interactive Scalar UI for testing endpoints directly from Odoo
- **OpenAPI 3.1.0** spec served at `/api/spec`
- **Beginner-friendly** — simple query params, helpful error messages

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/{model}` | Search & read records |
| `GET` | `/api/{model}/{id}` | Read single record |
| `PUT` | `/api/{model}` | Upsert (create/update by unique key) |
| `PUT` | `/api/{model}/{id}` | Update by ID |
| `DELETE` | `/api/{model}/{id}` | Delete record |
| `GET` | `/api/{model}/fields` | Field metadata (types, relations) |

## Quick Start

1. Install the module from Odoo Apps
2. Go to **REST API → API Console** in the backend menu
3. Click **Generate Token**
4. Start calling API endpoints

```bash
# Search partners
curl -H "Authorization: Bearer <token>" \
  "http://your-odoo.com/api/res.partner?limit=3&fields=name,email"

# Upsert partner (create if not exists)
curl -H "Authorization: Bearer <token>" \
  -X PUT "http://your-odoo.com/api/res.partner" \
  -H "Content-Type: application/json" \
  -d '{"_key":{"email":"john@example.com"},"name":"John Doe"}'

# Delete record
curl -H "Authorization: Bearer <token>" \
  -X DELETE "http://your-odoo.com/api/res.partner/1"
```

## Smart Relational Fields

Send names instead of IDs — the API auto-resolves them:

```json
PUT /api/product.product
{
  "_key": {"barcode": "12345"},
  "name": "New Product",
  "categ_id": "Electronics"
}
```

If "Electronics" doesn't exist, it's created automatically.

## Supported Models

Account, Journal, Move, Payment, Tax, CRM (Lead, Stage, Tag), HR (Department, Employee, Job), MRP (BOM, Production, Workorder), POS (Config, Order, Session), Product (Attribute, Category, Product, Template), Project, Purchase, Partner, Sale, Stock (Location, Move, Picking, Quant, Warehouse), UoM

## n8n Automation Integration

This module works perfectly with [n8n](https://n8n.io) for workflow automation. Use the [Odoo n8n Community Node](https://www.npmjs.com/package/@n8n-dev/n8n-nodes-odoo-v17) to connect n8n to your Odoo instance.

**Setup:**
1. Install this REST API module in Odoo
2. Generate a Bearer token from **REST API → API Console**
3. Install the Odoo node in n8n: `npm install @n8n-dev/n8n-nodes-odoo-v17`
4. Configure the Odoo node with your instance URL and token

**Example workflows:**
- Sync new Shopify orders → Odoo Sale Orders
- When CRM lead is won → Create Invoice automatically
- Daily stock report → Send to Slack/Telegram
- New employee in HR → Auto-create Odoo user + email welcome

## Requirements

- Odoo 17.0
- No external dependencies

## Support

- Documentation: [GitHub README](https://github.com/kelvinzer0/odoo-openapi-spec/blob/main/README-odoo-selfhost.md)
- Issues: [GitHub Issues](https://github.com/kelvinzer0/odoo-openapi-spec/issues)
