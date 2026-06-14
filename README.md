# REST API Gateway for Odoo

**Turn your Odoo into a powerful REST API in minutes.**

Stop wrestling with XML-RPC. REST API Gateway gives you clean, modern HTTP endpoints that any developer, tool, or automation platform can use instantly.

---

## Why REST API Gateway?

| Problem | Solution |
|---|---|
| XML-RPC is complex and outdated | Clean REST API with JSON |
| Sharing passwords for API access | Secure Bearer tokens from Odoo UI |
| Confused by Odoo field IDs | Send names — auto-resolves to IDs |
| No API documentation | Built-in Scalar UI for live testing |
| Hard to integrate with external tools | Works with n8n, Zapier, Make, mobile apps |

---

## Features

- **45+ Business Models** — Account, CRM, HR, Inventory, POS, Product, Sales, Stock, and more
- **Bearer Token Auth** — Generate secure tokens from Odoo backend, no password needed
- **Smart Upsert** — Create or update records in one API call using unique keys
- **Name-Based Relations** — Send `"categ_id": "Electronics"` instead of IDs
- **Interactive API Docs** — Scalar UI built-in for testing endpoints live
- **OpenAPI 3.1.0** — Industry-standard spec for code generation
- **Field Explorer** — See all field types, relations, and required fields
- **Beginner Friendly** — Clear error messages guide you to the right fields

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/{model}` | Search & read records |
| `GET` | `/api/{model}/{id}` | Read single record |
| `PUT` | `/api/{model}` | Upsert (create/update by key) |
| `PUT` | `/api/{model}/{id}` | Update by ID |
| `DELETE` | `/api/{model}/{id}` | Delete record |
| `GET` | `/api/{model}/fields` | Field metadata |

---

## Quick Start

**1. Install** from Odoo Apps

**2. Generate Token** — Go to REST API → API Console → Click "Generate Token"

**3. Start Using:**

```bash
# Search partners
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://odoo.warunglakku.com/api/res.partner?limit=5&fields=name,email"

# Upsert partner (create if not exists)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -X PUT "https://odoo.warunglakku.com/api/res.partner" \
  -H "Content-Type: application/json" \
  -d '{"_key":{"email":"john@example.com"},"name":"John Doe","phone":"+628123456"}'

# Get field metadata
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://odoo.warunglakku.com/api/product.product/fields"
```

---

## Use Cases

| Integration | How It Helps |
|---|---|
| **E-commerce** | Sync Shopify/WooCommerce orders with Odoo |
| **Mobile Apps** | Power iOS/Android with real-time Odoo data |
| **n8n / Make / Zapier** | Automate workflows across 1000+ apps |
| **BI Tools** | Connect Power BI, Tableau, Metabase |
| **Custom Frontend** | Build React/Vue/Next.js admin panels |

---

## n8n Automation Ready

```bash
npm install @n8n-dev/n8n-nodes-odoo-v17
```

Example workflows:
- New Shopify order → Create Odoo Sale Order
- CRM lead marked won → Auto-generate Invoice
- Daily stock levels → Send report to Slack
- New employee in HR → Auto-create Odoo user

---

## Supported Models

Account, Journal, Move, Payment, Tax, CRM (Lead, Stage, Tag), HR (Department, Employee, Job), MRP (BOM, Production, Workorder), POS (Config, Order, Session), Product (Attribute, Category, Product, Template), Project, Purchase, Partner, Sale, Stock (Location, Move, Picking, Quant, Warehouse), UoM

---

## Live Demo

**Try it now:** [https://odoo.warunglakku.com](https://odoo.warunglakku.com)

1. Login with demo credentials
2. Go to REST API → API Console
3. Generate a token
4. Test the API endpoints

---

## What You Get

- REST API controller with full CRUD operations
- API Console with interactive Scalar documentation
- OpenAPI 3.1.0 specification
- Bearer token management UI
- Field metadata explorer
- Smart relational field resolver
- Comprehensive error handling
- No hidden fees, no activation keys

---

## Requirements

- Odoo 17.0
- No external dependencies

---

## Support

- **Live Demo:** [odoo.warunglakku.com](https://odoo.warunglakku.com)
- **Documentation:** [GitHub](https://github.com/kelvinzer0/odoo-openapi-spec/blob/main/README-odoo-selfhost.md)
- **Issues:** [GitHub Issues](https://github.com/kelvinzer0/odoo-openapi-spec/issues)
- **Email:** kelvinandriancom@gmail.com
