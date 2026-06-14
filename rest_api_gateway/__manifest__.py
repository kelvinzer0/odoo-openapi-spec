{
    'name': 'REST API Gateway',
    'version': '17.0.1.0.0',
    'summary': 'Turn Odoo into a powerful REST API with Bearer token auth, upsert, and interactive docs',
    'description': '''
Transform your Odoo instance into a fully-featured REST API gateway.

Why Choose REST API Gateway?

Stop struggling with Odoo's complex XML-RPC. Our module gives you a clean, modern REST API that any developer or tool can use in minutes.

KEY FEATURES:

- Instant API Access: Expose 45+ business models as REST endpoints
- Zero-Config Auth: Generate Bearer tokens from the Odoo UI — no password sharing
- Smart Upsert: Create or update records in one call using unique keys
- Name-Based Relations: Send "Electronics" instead of category IDs — auto-resolves
- Interactive Docs: Built-in Scalar UI for testing endpoints live from your browser
- OpenAPI 3.1.0: Industry-standard spec for code generation and tooling
- Field Explorer: See all field types, relations, and required fields instantly
- Beginner Friendly: Clear error messages guide you to the right fields

PERFECT FOR:

- E-commerce Integration: Connect Shopify, WooCommerce, or any platform
- Mobile App Backend: Power iOS/Android apps with Odoo data
- n8n/Make/Zapier Workflows: Automate across 1000+ apps
- Third-Party Tools: Connect Power BI, Tableau, or custom dashboards
- Microservices Architecture: Decouple frontend from Odoo backend

SUPPORTED MODELS:

Account, CRM, HR, Inventory, Manufacturing, POS, Product, Purchase, Sales, Stock, Projects, and more — 45 business models ready to go.

ENDPOINTS:

- GET /api/{model} — Search & read records
- GET /api/{model}/{id} — Read single record
- PUT /api/{model} — Upsert (create or update)
- PUT /api/{model}/{id} — Update by ID
- DELETE /api/{model}/{id} — Delete record
- GET /api/{model}/fields — Field metadata

AUTHENTICATION:

- Bearer Token (recommended) — Generate from API Console
- HTTP Basic Auth — Email + password

WHAT'S INCLUDED:

- REST API controller with full CRUD operations
- API Console with Scalar documentation
- OpenAPI 3.1.0 specification
- Bearer token management UI
- Field metadata explorer
- Smart relational field resolver
- Comprehensive error handling

NO HIDDEN FEES. NO ACTIVATION KEYS. YOUR DATA STAYS YOURS.

Requirements: Odoo 17.0
    ''',
    'category': 'Technical',
    'author': 'Warung Lakku',
    'website': 'https://odoo.warunglakku.com',
    'license': 'LGPL-3',
    'price': 100.00,
    'currency': 'USD',
    'images': ['images/main_screenshot.png'],
    'depends': ['base'],
    'data': [
        'views/credentials_template.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'support': 'kelvinandriancom@gmail.com',
    'live_test_url': 'https://odoo.warunglakku.com',
}
