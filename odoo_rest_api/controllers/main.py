import json
import functools
import base64

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


def json_response(data, status=200):
    return Response(
        json.dumps(data),
        status=status,
        content_type='application/json',
    )


def error_response(message, status=400):
    return json_response({'error': message}, status=status)


def authenticate():
    auth = request.httprequest.headers.get('Authorization', '')
    if not auth.startswith('Basic '):
        return None, None

    try:
        decoded = base64.b64decode(auth[6:]).decode()
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
        request.uid = uid
        request.auth_password = password
        return func(*args, **kwargs)
    return wrapper


class RestApiController(http.Controller):

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
