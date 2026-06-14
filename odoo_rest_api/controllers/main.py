import json
import functools
import base64
import secrets
import os
from datetime import date, datetime

from odoo import http
from odoo.http import request, Response


# ── Unique key per model (verified against live Odoo 17 instance) ──
MODEL_KEYS = {
    'account.account':         ['code'],
    'account.journal':         ['code'],
    'account.move':            ['name'],
    'account.move.line':       ['name'],
    'account.payment':         ['name'],
    'account.tax':             ['name'],
    'account.tax.group':       ['name'],
    'crm.lead':                ['name'],
    'crm.stage':               ['name'],
    'crm.tag':                 ['name'],
    'hr.department':           ['name'],
    'hr.employee':             ['work_email'],
    'hr.job':                  ['name'],
    'mail.message':            ['subject'],
    'mail.thread':             ['id'],
    'mrp.bom':                 ['code'],
    'mrp.production':          ['name'],
    'mrp.workorder':           ['name'],
    'pos.config':              ['name'],
    'pos.order':               ['name'],
    'pos.order.line':          ['name'],
    'pos.session':             ['name'],
    'product.attribute':       ['name'],
    'product.attribute.value': ['name'],
    'product.category':        ['name'],
    'product.product':         ['barcode'],
    'product.template':        ['name'],
    'project.project':         ['name'],
    'project.task':            ['name'],
    'purchase.order':          ['name'],
    'purchase.order.line':     ['name'],
    'res.partner':             ['email'],
    'res.partner.bank':        ['acc_number'],
    'res.partner.category':    ['name'],
    'sale.order':              ['name'],
    'sale.order.line':         ['name'],
    'stock.location':          ['complete_name'],
    'stock.move':              ['name'],
    'stock.move.line':         ['name'],
    'stock.picking':           ['name'],
    'stock.picking.type':      ['name'],
    'stock.quant':             ['id'],
    'stock.warehouse':         ['name'],
    'uom.category':            ['name'],
    'uom.uom':                 ['name'],
}

TOKEN_PREFIX = 'odoo-rest-api:'


def json_response(data, status=200):
    return Response(
        json.dumps(data, default=str),
        status=status,
        content_type='application/json',
    )


def error_response(message, status=400):
    return json_response({'error': message}, status=status)


def _get_token_key(user_id):
    return f'{TOKEN_PREFIX}{user_id}'


def authenticate():
    auth = request.httprequest.headers.get('Authorization', '')

    if auth.startswith('Bearer '):
        token = auth[7:]
        return _authenticate_bearer(token)

    if auth.startswith('Basic '):
        return _authenticate_basic(auth[6:])

    return None, None


def _authenticate_bearer(token):
    IParam = request.env['ir.config_parameter'].with_context(active_test=False).sudo()

    keys = IParam.search([('key', '=like', f'{TOKEN_PREFIX}%')])
    for key_rec in keys:
        stored_token = key_rec.value
        if secrets.compare_digest(stored_token, token):
            user_id = int(key_rec.key.split(':')[-1])
            user = request.env['res.users'].sudo().browse(user_id)
            if user.exists() and user.active:
                return user.id, None

    return None, None


def _authenticate_basic(encoded):
    try:
        decoded = base64.b64decode(encoded).decode()
        email, password = decoded.split(':', 1)
    except Exception:
        return None, None

    db = request.session.db or request.httprequest.host.split(':')[0]
    try:
        uid = request.session.authenticate(db, email, password)
    except Exception:
        return None, None

    return uid, password


def with_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        uid, password = authenticate()
        if not uid:
            return error_response('Unauthorized', 401)
        request.update_env(user=uid)
        return func(*args, **kwargs)
    return wrapper


def _resolve_relational(model_name, data):
    Model = request.env[model_name].sudo()
    fields_get = Model.fields_get()
    resolved = {}

    for fname, value in data.items():
        if fname not in fields_get:
            resolved[fname] = value
            continue

        finfo = fields_get[fname]
        rel = finfo.get('relation')
        ftype = finfo.get('type')

        if ftype == 'many2one' and rel:
            if isinstance(value, int):
                resolved[fname] = value
            elif isinstance(value, str) and value.strip():
                rel_model = request.env[rel].sudo()
                search_fields = ['name']
                if 'complete_name' in rel_model._fields:
                    search_fields.append('complete_name')
                domain = ['|'] * (len(search_fields) - 1)
                for sf in search_fields:
                    domain.extend([(sf, '=', value)])
                rec = rel_model.search(domain, limit=1)
                if rec:
                    resolved[fname] = rec.id
                else:
                    new_rec = rel_model.create({'name': value})
                    resolved[fname] = new_rec.id
            elif isinstance(value, dict):
                rel_model = request.env[rel].sudo()
                domain = [(k, '=', v) for k, v in value.items()]
                rec = rel_model.search(domain, limit=1)
                if rec:
                    resolved[fname] = rec.id
                else:
                    new_rec = rel_model.create(value)
                    resolved[fname] = new_rec.id
            else:
                resolved[fname] = value

        elif ftype in ('many2many', 'one2many') and rel:
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    rel_model = request.env[rel].sudo()
                    ids = []
                    for item in value:
                        if isinstance(item, dict):
                            if 'id' in item:
                                ids.append(item['id'])
                            else:
                                domain = [(k, '=', v) for k, v in item.items()]
                                rec = rel_model.search(domain, limit=1)
                                if rec:
                                    ids.append(rec.id)
                                else:
                                    new_rec = rel_model.create(item)
                                    ids.append(new_rec.id)
                    resolved[fname] = [(6, 0, ids)] if ftype == 'many2many' else ids
                elif isinstance(value[0], int):
                    resolved[fname] = [(6, 0, value)] if ftype == 'many2many' else value
                else:
                    resolved[fname] = value
            elif isinstance(value, str) and value.strip():
                rel_model = request.env[rel].sudo()
                search_fields = ['name']
                if 'complete_name' in rel_model._fields:
                    search_fields.append('complete_name')
                domain = ['|'] * (len(search_fields) - 1)
                for sf in search_fields:
                    domain.extend([(sf, '=', value)])
                rec = rel_model.search(domain, limit=1)
                if rec:
                    resolved[fname] = [(6, 0, [rec.id])] if ftype == 'many2many' else [rec.id]
                else:
                    new_rec = rel_model.create({'name': value})
                    resolved[fname] = [(6, 0, [new_rec.id])] if ftype == 'many2many' else [new_rec.id]
            else:
                resolved[fname] = value
        else:
            resolved[fname] = value

    return resolved


class RestApiController(http.Controller):

    # ═══════════════════════════════════════════
    # Credentials UI
    # ═══════════════════════════════════════════
    @http.route('/api/credentials', type='http', auth='user')
    def credentials_page(self, **kwargs):
        user = request.env.user
        name = user.name or ''
        initials = ''.join(w[0].upper() for w in name.split()[:2]) if name else '?'
        return request.render('odoo_rest_api.credentials_page', {
            'user_email': user.email or '',
            'user_name': name,
            'user_initial': initials,
        })

    @http.route('/api/credentials/check', type='json', auth='user', csrf=False)
    def check_token(self, **kwargs):
        user_id = request.env.user.id
        ICP = request.env['ir.config_parameter'].sudo()
        key = _get_token_key(user_id)
        token = ICP.get_param(key)
        if token:
            return {'has_token': True, 'token_preview': token[:8] + '...' + token[-4:]}
        return {'has_token': False}

    @http.route('/api/credentials/generate', type='json', auth='user', methods=['POST'], csrf=False)
    def generate_token(self, **kwargs):
        user_id = request.env.user.id
        ICP = request.env['ir.config_parameter'].sudo()
        key = _get_token_key(user_id)

        token = secrets.token_urlsafe(32)
        ICP.set_param(key, token)

        return {'token': f'Bearer {token}'}

    @http.route('/api/credentials/revoke', type='json', auth='user', methods=['POST'], csrf=False)
    def revoke_token(self, **kwargs):
        user_id = request.env.user.id
        ICP = request.env['ir.config_parameter'].sudo()
        key = _get_token_key(user_id)
        ICP.set_param(key, '')
        return {'revoked': True}

    # ═══════════════════════════════════════════
    # Fields Metadata
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>/fields', type='http', auth='none', methods=['GET'], csrf=False)
    @with_auth
    def fields(self, model, **kwargs):
        try:
            Model = request.env[model].sudo()
            fields_get = Model.fields_get()
            result = {}
            for fname, finfo in fields_get.items():
                rel = finfo.get('relation')
                entry = {
                    'type': finfo.get('type'),
                    'label': finfo.get('string', ''),
                    'required': finfo.get('required', False),
                }
                if rel:
                    entry['relation'] = rel
                    entry['help'] = f'Send {{\"{fname}\": \"Name\"}} to auto-resolve ID'
                if finfo.get('selection'):
                    entry['selection'] = finfo['selection']
                result[fname] = entry
            return json_response(result)
        except Exception as e:
            return error_response(str(e), 500)

    # ═══════════════════════════════════════════
    # OpenAPI Spec
    # ═══════════════════════════════════════════
    def _read_spec(self, filename):
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'spec', filename)
        with open(spec_path, 'r') as f:
            return f.read()

    @http.route('/api/spec', type='http', auth='none', methods=['GET'], csrf=False)
    def spec_full(self, **kwargs):
        data = self._read_spec('odoo-openapi.json')
        return Response(data, content_type='application/json')

    @http.route('/api/spec/compact', type='http', auth='none', methods=['GET'], csrf=False)
    def spec_compact(self, **kwargs):
        data = self._read_spec('odoo-openapi-compact.json')
        return Response(data, content_type='application/json')

    @http.route('/api/spec/docs', type='http', auth='none', methods=['GET'], csrf=False)
    def spec_docs(self, **kwargs):
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>Odoo REST API Docs</title>
    <style>body { margin: 0; padding: 0; }</style>
</head>
<body>
    <script id="api-reference" data-url="/api/spec/compact"></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
</body>
</html>'''
        return Response(html, content_type='text/html')

    # ═══════════════════════════════════════════
    # GET /api/{model} — search_read
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>', type='http', auth='none', methods=['GET'], csrf=False)
    @with_auth
    def search(self, model, **kwargs):
        try:
            domain = json.loads(kwargs.get('domain', '[]'))
        except json.JSONDecodeError:
            return error_response('Invalid domain JSON')

        fields_str = kwargs.get('fields', '')
        limit = int(kwargs.get('limit', 20))
        offset = int(kwargs.get('offset', 0))
        order = kwargs.get('order', '')

        kwargs_read = {'limit': limit, 'offset': offset}
        if fields_str:
            kwargs_read['fields'] = [f.strip() for f in fields_str.split(',')]
        if order:
            kwargs_read['order'] = order

        try:
            Model = request.env[model].sudo()
            records = Model.search_read(domain, **kwargs_read)
            return json_response({'count': len(records), 'records': records})
        except Exception as e:
            return error_response(str(e), 500)

    # ═══════════════════════════════════════════
    # GET /api/{model}/{id} — read single
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>/<int:record_id>', type='http', auth='none', methods=['GET'], csrf=False)
    @with_auth
    def read(self, model, record_id, **kwargs):
        try:
            Model = request.env[model].sudo()
            record = Model.browse(record_id)
            if not record.exists():
                return error_response(f'{model} id={record_id} not found', 404)
            return json_response(record.read()[0])
        except Exception as e:
            return error_response(str(e), 500)

    # ═══════════════════════════════════════════
    # PUT /api/{model} — upsert (by _key)
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>', type='http', auth='none', methods=['PUT'], csrf=False)
    @with_auth
    def upsert(self, model, **kwargs):
        try:
            body = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return error_response('Invalid JSON body')

        if '_key' not in body:
            return error_response('Missing _key in request body')

        key_fields = MODEL_KEYS.get(model, ['name'])
        key_data = body['_key']
        data = {k: v for k, v in body.items() if k != '_key'}
        data = _resolve_relational(model, data)

        domain = []
        for kf in key_fields:
            val = key_data.get(kf)
            if val is None:
                return error_response(f'Missing key field: {kf}')
            domain.append((kf, '=', val))

        try:
            Model = request.env[model].sudo()
            existing = Model.search(domain, limit=1)

            if existing:
                existing.write(data)
                return json_response({
                    'id': existing.id,
                    'created': False,
                    'matched_by': str(key_data),
                })
            else:
                data.update(key_data)
                new_record = Model.create(data)
                return json_response({
                    'id': new_record.id,
                    'created': True,
                    'matched_by': None,
                })
        except Exception as e:
            return error_response(str(e), 500)

    # ═══════════════════════════════════════════
    # PUT /api/{model}/{id} — update by ID
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>/<int:record_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    @with_auth
    def update(self, model, record_id, **kwargs):
        try:
            body = json.loads(request.httprequest.data)
        except json.JSONDecodeError:
            return error_response('Invalid JSON body')

        body = _resolve_relational(model, body)

        try:
            Model = request.env[model].sudo()
            record = Model.browse(record_id)
            if not record.exists():
                return error_response(f'{model} id={record_id} not found', 404)
            record.write(body)
            return json_response({'id': record_id, 'created': False})
        except Exception as e:
            return error_response(str(e), 500)

    # ═══════════════════════════════════════════
    # DELETE /api/{model}/{id} — unlink
    # ═══════════════════════════════════════════
    @http.route('/api/<path:model>/<int:record_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    @with_auth
    def delete(self, model, record_id, **kwargs):
        try:
            Model = request.env[model].sudo()
            record = Model.browse(record_id)
            if not record.exists():
                return error_response(f'{model} id={record_id} not found', 404)
            record.unlink()
            return json_response({'id': record_id, 'deleted': True})
        except Exception as e:
            return error_response(str(e), 500)
