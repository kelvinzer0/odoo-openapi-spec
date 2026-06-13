# Odoo OpenAPI Spec

Auto-generated OpenAPI 3.1.0 specification from Odoo 17.0 instance.

## Files

| File | Size | Paths | Description |
|---|---|---|---|
| `odoo-openapi.json` | ~11 MB | 1,407 | Full spec — all 494 models |
| `odoo-openapi-compact.json` | ~2.3 MB | 135 | Business models only |
| `odoo-openapi-generator.py` | — | — | Generator script (reusable) |

## Models Included (Compact)

Product, Partner, Sale, Purchase, Account/Invoice, Stock, CRM, POS, HR, MRP, Project, UoM

## Endpoint Pattern

| Method | Path | Odoo Method |
|---|---|---|
| `GET` | `/api/{model}` | `search_read()` |
| `POST` | `/api/{model}` | `create()` |
| `GET` | `/api/{model}/{id}` | `read()` |
| `PUT` | `/api/{model}/{id}` | `write()` |
| `DELETE` | `/api/{model}/{id}` | `unlink()` |
| `POST` | `/api/{model}/{id}/call` | `execute_kw()` |

## Regenerate

```bash
python3 odoo-openapi-generator.py > odoo-openapi.json
```

Edit the config in the script (URL, DB, USER, PASS) to point to your Odoo instance.

## Odoo Version

```
Server: 17.0
```
