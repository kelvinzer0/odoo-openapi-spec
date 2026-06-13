{
    'name': 'REST API',
    'version': '17.0.1.0.0',
    'summary': 'REST API for Odoo models with Bearer token & upsert support',
    'description': '''
        Exposes Odoo models as REST endpoints:

        - GET    /api/<model>          → search & read
        - GET    /api/<model>/<id>     → read single record
        - PUT    /api/<model>          → upsert (create or update by unique key)
        - PUT    /api/<model>/<id>     → update by ID
        - DELETE /api/<model>/<id>     → delete record

        Authentication: Bearer token (generated from /api/credentials)
        or HTTP Basic Auth (Odoo user email + password).
    ''',
    'category': 'Technical',
    'author': 'Warung Lakku',
    'website': 'https://odoo.warunglakku.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'views/credentials_template.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
