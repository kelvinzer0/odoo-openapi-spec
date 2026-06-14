{
    'name': 'REST API Gateway',
    'version': '17.0.1.0.0',
    'summary': 'Expose Odoo models as REST API with Bearer token auth, upsert, and Scalar docs',
    'description': '''
Expose any Odoo model as REST API endpoints.

Features:
- REST API for 45 business models
- Bearer token authentication (generate from UI)
- Upsert support (create/update by unique key)
- Smart relational fields (send names, auto-resolve IDs)
- Interactive API documentation (Scalar UI)
- OpenAPI 3.1.0 spec served at /api/spec
- Field metadata endpoint (/api/{model}/fields)
- Beginner-friendly error messages

Endpoints:
- GET    /api/<model>          → search & read records
- GET    /api/<model>/<id>     → read single record
- PUT    /api/<model>          → upsert (create or update by unique key)
- PUT    /api/<model>/<id>     → update by ID
- DELETE /api/<model>/<id>     → delete record
- GET    /api/<model>/fields   → field metadata

Authentication:
- Bearer token (recommended, generated from /api/credentials)
- HTTP Basic Auth (email:password)
    ''',
    'category': 'Technical',
    'author': 'Warung Lakku',
    'website': 'https://github.com/kelvinzer0/odoo-openapi-spec',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'views/credentials_template.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'support': 'kelvinandriancom@gmail.com',
}
