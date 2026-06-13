import xmlrpc.client
import ssl
import json
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
import copy
import secrets

app = FastAPI(
    title="Odoo REST API Proxy",
    description="REST-to-XML-RPC proxy for Odoo. Translates REST calls to Odoo XML-RPC.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# ── Config ──
ODOO_URL = "https://odoo.warunglakku.com"
ODOO_DB = "warunglakku-odoo"

# ── Unique key per model ──
MODEL_KEYS = {
    "account.account": ["code"],
    "account.journal": ["code"],
    "account.move": ["name"],
    "account.move.line": ["name"],
    "account.payment": ["name"],
    "account.tax": ["name"],
    "account.tax.group": ["name"],
    "crm.lead": ["name"],
    "crm.stage": ["name"],
    "crm.tag": ["name"],
    "hr.department": ["name"],
    "hr.employee": ["work_email"],
    "hr.job": ["name"],
    "mail.message": ["subject"],
    "mail.thread": ["id"],
    "mrp.bom": ["code"],
    "mrp.production": ["name"],
    "mrp.workorder": ["name"],
    "pos.config": ["name"],
    "pos.order": ["name"],
    "pos.order.line": ["name"],
    "pos.session": ["name"],
    "product.attribute": ["name"],
    "product.attribute.value": ["name"],
    "product.category": ["name"],
    "product.product": ["barcode"],
    "product.template": ["name"],
    "project.project": ["name"],
    "project.task": ["name"],
    "purchase.order": ["name"],
    "purchase.order.line": ["name"],
    "res.partner": ["email"],
    "res.partner.bank": ["acc_number"],
    "res.partner.category": ["name"],
    "sale.order": ["name"],
    "sale.order.line": ["name"],
    "stock.location": ["complete_name"],
    "stock.move": ["name"],
    "stock.move.line": ["name"],
    "stock.picking": ["name"],
    "stock.picking.type": ["name"],
    "stock.quant": ["id"],
    "stock.warehouse": ["name"],
    "uom.category": ["name"],
    "uom.uom": ["name"],
}


def get_odoo(credentials: HTTPBasicCredentials = Depends(security)):
    ctx = ssl.create_default_context()
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", context=ctx)
    uid = common.authenticate(ODOO_DB, credentials.username, credentials.password, {})
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid Odoo credentials")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)
    return {
        "uid": uid,
        "password": credentials.password,
        "models": models,
    }


# ═══════════════════════════════════════════
# GET /api/{model} — search_read
# ═══════════════════════════════════════════
@app.get("/api/{model:path}")
def search_model(
    model: str,
    request: Request,
    domain: str = "[]",
    fields: str = "",
    limit: int = 20,
    offset: int = 0,
    order: str = "",
    odoo=Depends(get_odoo),
):
    try:
        domain_list = json.loads(domain) if domain else []
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid domain JSON")

    kwargs = {"limit": limit, "offset": offset}
    if fields:
        kwargs["fields"] = [f.strip() for f in fields.split(",")]
    if order:
        kwargs["order"] = order

    try:
        records = odoo["models"].execute_kw(
            ODOO_DB, odoo["uid"], odoo["password"],
            model, "search_read", [domain_list], kwargs,
        )
        return {"count": len(records), "records": records}
    except Exception as e:
        raise HTTPException(500, detail=str(e)[:500])


# ═══════════════════════════════════════════
# GET /api/{model}/{id} — read single
# ═══════════════════════════════════════════
@app.get("/api/{model:path}/{record_id:int}")
def read_model(model: str, record_id: int, fields: str = "", odoo=Depends(get_odoo)):
    kwargs = {}
    if fields:
        kwargs["fields"] = [f.strip() for f in fields.split(",")]

    try:
        records = odoo["models"].execute_kw(
            ODOO_DB, odoo["uid"], odoo["password"],
            model, "read", [[record_id]], kwargs,
        )
        if not records:
            raise HTTPException(404, f"{model} id={record_id} not found")
        return records[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e)[:500])


# ═══════════════════════════════════════════
# PUT /api/{model} — upsert (by _key)
# ═══════════════════════════════════════════
@app.put("/api/{model:path}")
async def upsert_model(model: str, request: Request, odoo=Depends(get_odoo)):
    body = await request.json()

    if "_key" not in body:
        raise HTTPException(400, "Missing _key in request body")

    key_fields = MODEL_KEYS.get(model, ["name"])
    key_data = body["_key"]
    data = {k: v for k, v in body.items() if k != "_key"}

    domain = []
    for kf in key_fields:
        val = key_data.get(kf)
        if val is None:
            raise HTTPException(400, f"Missing key field: {kf}")
        domain.append([kf, "=", val])

    try:
        existing = odoo["models"].execute_kw(
            ODOO_DB, odoo["uid"], odoo["password"],
            model, "search", [domain], {"limit": 1},
        )

        if existing:
            rid = existing[0]
            odoo["models"].execute_kw(
                ODOO_DB, odoo["uid"], odoo["password"],
                model, "write", [[rid], data],
            )
            return {"id": rid, "created": False, "matched_by": str(key_data)}
        else:
            data.update(key_data)
            new_id = odoo["models"].execute_kw(
                ODOO_DB, odoo["uid"], odoo["password"],
                model, "create", [data],
            )
            return {"id": new_id, "created": True, "matched_by": None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e)[:500])


# ═══════════════════════════════════════════
# PUT /api/{model}/{id} — update by ID
# ═══════════════════════════════════════════
@app.put("/api/{model:path}/{record_id:int}")
async def update_model(model: str, record_id: int, request: Request, odoo=Depends(get_odoo)):
    data = await request.json()
    try:
        odoo["models"].execute_kw(
            ODOO_DB, odoo["uid"], odoo["password"],
            model, "write", [[record_id], data],
        )
        return {"id": record_id, "created": False}
    except Exception as e:
        raise HTTPException(500, detail=str(e)[:500])


# ═══════════════════════════════════════════
# DELETE /api/{model}/{id} — unlink
# ═══════════════════════════════════════════
@app.delete("/api/{model:path}/{record_id:int}")
def delete_model(model: str, record_id: int, odoo=Depends(get_odoo)):
    try:
        odoo["models"].execute_kw(
            ODOO_DB, odoo["uid"], odoo["password"],
            model, "unlink", [[record_id]],
        )
        return {"id": record_id, "deleted": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e)[:500])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
