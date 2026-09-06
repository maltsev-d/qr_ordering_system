import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from db.database import (CategoryDB, DishDB, ModifierGroupDB, OrderDB,
                         OrderItemDB, RestaurantDB, TableDB, WaiterCallDB,
                         create_tables, get_db)
from db.models import (CallWaiterRequest, OrderStatus, UpdateOrderStatusRequest)

load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

app = FastAPI(title="Sabaidee Kitchen", version="3.0.0")

create_tables()

os.makedirs("static", exist_ok=True)
os.makedirs("templates/admin", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── Helpers ───

LANG_FIELD_MAP = {
    "en": "en", "zh": "cn", "th": "th",
    "ru": "ru", "ko": "ko", "fr": "fr",
    "lo": "lo", "ar": "ar",
}


def lang_field(lang: str) -> str:
    return LANG_FIELD_MAP.get(lang, "en")


async def send_telegram(text: str):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={
                "chat_id": TG_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            })
        except Exception as e:
            print(f"TG error: {e}")


def build_modifier_label(item: OrderItemDB, lang: str) -> str:
    if not item.modifiers_json or not item.dish:
        return ""
    try:
        mods = json.loads(item.modifiers_json)
    except Exception:
        return ""
    lf = lang_field(lang)
    labels = []
    for mg in item.dish.modifier_groups:
        mod_id = mods.get(str(mg.id))
        if mod_id:
            mod = next((m for m in mg.modifiers if str(m.id) == str(mod_id)), None)
            if mod:
                label = getattr(mod, f"label_{lf}", None) or mod.label_en
                labels.append((mod.emoji or "") + " " + label)
    return ", ".join(labels)


# ─── Customer Routes ───

@app.get("/menu/{restaurant_id}/{table_id}", response_class=HTMLResponse)
async def menu(
        request: Request,
        restaurant_id: int,
        table_id: int,
        lang: str = None,
        db: Session = Depends(get_db)
):
    restaurant = db.query(RestaurantDB).filter(RestaurantDB.id == restaurant_id).first()
    table = db.query(TableDB).filter(TableDB.id == table_id).first()

    if not restaurant or not table:
        raise HTTPException(status_code=404, detail="Not found")

    categories = db.query(CategoryDB).filter(
        CategoryDB.restaurant_id == restaurant_id
    ).order_by(CategoryDB.sort_order).all()

    dishes = db.query(DishDB).options(
        joinedload(DishDB.modifier_groups).joinedload(ModifierGroupDB.modifiers)
    ).filter(
        DishDB.category_id.in_([c.id for c in categories]),
        DishDB.active == True
    ).order_by(DishDB.sort_order).all()

    def dish_to_dict(d):
        return {
            "id": d.id, "category_id": d.category_id,
            "active": d.active, "price": d.price,
            "photo_url": d.photo_url,
            "is_surprise_eligible": d.is_surprise_eligible,
            "name_en": d.name_en, "name_lo": d.name_lo,
            "name_cn": d.name_cn, "name_ru": d.name_ru,
            "name_th": d.name_th, "name_ko": d.name_ko,
            "name_fr": d.name_fr, "name_ar": d.name_ar,
            "desc_en": d.desc_en, "desc_lo": d.desc_lo,
            "desc_cn": d.desc_cn, "desc_ru": d.desc_ru,
            "desc_th": d.desc_th, "desc_ko": d.desc_ko,
            "desc_fr": d.desc_fr, "desc_ar": d.desc_ar,
            "modifier_groups": [
                {
                    "id": mg.id, "dish_id": mg.dish_id,
                    "name_en": mg.name_en, "name_lo": mg.name_lo,
                    "name_cn": mg.name_cn, "name_ru": mg.name_ru,
                    "name_th": mg.name_th, "name_ko": mg.name_ko,
                    "name_fr": mg.name_fr, "name_ar": mg.name_ar,
                    "required": mg.required,
                    "modifiers": [
                        {
                            "id": m.id, "emoji": m.emoji,
                            "label_en": m.label_en, "label_lo": m.label_lo,
                            "label_cn": m.label_cn, "label_ru": m.label_ru,
                            "label_th": m.label_th, "label_ko": m.label_ko,
                            "label_fr": m.label_fr, "label_ar": m.label_ar,
                            "price_add": m.price_add
                        } for m in mg.modifiers
                    ]
                } for mg in d.modifier_groups
            ]
        }

    def cat_to_dict(c):
        return {
            "id": c.id, "sort_order": c.sort_order,
            "name_en": c.name_en, "name_lo": c.name_lo,
            "name_cn": c.name_cn, "name_ru": c.name_ru,
            "name_th": c.name_th, "name_ko": c.name_ko,
            "name_fr": c.name_fr, "name_ar": c.name_ar,
        }

    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={
            "restaurant": restaurant,
            "table": table,
            "lang": lang,
            "categories_json": json.dumps([cat_to_dict(c) for c in categories]),
            "dishes_json": json.dumps([dish_to_dict(d) for d in dishes]),
        }
    )


@app.post("/order")
async def create_order(
        request: Request,
        restaurant_id: int = Form(...),
        table_id: int = Form(...),
        order_type: str = Form(...),
        items: str = Form(...),
        lang: str = Form(default="en"),
        db: Session = Depends(get_db)
):
    items_data = json.loads(items)

    restaurant = db.query(RestaurantDB).filter(RestaurantDB.id == restaurant_id).first()
    table = db.query(TableDB).filter(TableDB.id == table_id).first()

    if not restaurant or not table:
        raise HTTPException(status_code=404, detail="Not found")

    order = OrderDB(
        restaurant_id=restaurant_id,
        table_id=table_id,
        order_type=order_type,
        status=OrderStatus.NEW,
        total=0
    )
    db.add(order)
    db.flush()

    total = 0
    for item_data in items_data:
        dish = db.query(DishDB).filter(DishDB.id == item_data["dish_id"]).first()
        if not dish:
            continue
        qty = item_data.get("qty", 1)
        subtotal = dish.price * qty
        total += subtotal

        order_item = OrderItemDB(
            order_id=order.id,
            dish_id=dish.id,
            qty=qty,
            modifiers_json=json.dumps(item_data.get("modifiers", {})),
            subtotal=subtotal
        )
        db.add(order_item)

    order.total = total
    db.commit()

    # Перезагрузить с dish для TG
    order_with_items = db.query(OrderDB).options(
        joinedload(OrderDB.items).joinedload(OrderItemDB.dish)
    ).filter(OrderDB.id == order.id).first()

    items_text = "\n".join([
        f"• {i.dish.name_en} × {i.qty} — {i.subtotal:,} ₭"
        for i in order_with_items.items if i.dish
    ])
    order_type_label = "🍽️ Dine-in" if order_type == "dine_in" else "🥡 Takeaway"

    await send_telegram(
        f"🆕 <b>New order / ຄໍາສັ່ງໃໝ່ #{order.id:03d}</b>\n"
        f"Table / ໂຕະ {table.number} · {order_type_label}\n\n"
        f"{items_text}\n\n"
        f"<b>Total / ລວມ: {order.total:,} ₭</b>"
    )

    return RedirectResponse(url=f"/order-done/{order.id}?lang={lang}", status_code=303)


@app.get("/order-done/{order_id}", response_class=HTMLResponse)
async def order_done(
        request: Request,
        order_id: int,
        lang: str = "en",
        db: Session = Depends(get_db)
):
    order = db.query(OrderDB).options(
        joinedload(OrderDB.items).joinedload(OrderItemDB.dish).joinedload(
            DishDB.modifier_groups).joinedload(ModifierGroupDB.modifiers)
    ).filter(OrderDB.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    restaurant = db.query(RestaurantDB).filter(
        RestaurantDB.id == order.restaurant_id
    ).first()

    table = db.query(TableDB).filter(
        TableDB.id == order.table_id
    ).first()

    lf = lang_field(lang)
    for item in order.items:
        item.modifier_label = build_modifier_label(item, lang)
        if item.dish:
            item.dish_name = getattr(item.dish, f"name_{lf}", None) or item.dish.name_en

    return templates.TemplateResponse(
        request=request,
        name="order_done.html",
        context={
            "order": order,
            "restaurant": restaurant,
            "table": table,
            "lang": lang,
        }
    )


# ─── API: Customer ───

@app.post("/api/call-waiter")
async def call_waiter(
        request: CallWaiterRequest,
        db: Session = Depends(get_db)
):
    restaurant = db.query(RestaurantDB).filter(RestaurantDB.id == request.restaurant_id).first()
    table = db.query(TableDB).filter(TableDB.id == request.table_id).first()

    if not restaurant or not table:
        raise HTTPException(status_code=404, detail="Not found")

    recent_call = db.query(WaiterCallDB).filter(
        WaiterCallDB.restaurant_id == request.restaurant_id,
        WaiterCallDB.table_id == request.table_id,
        WaiterCallDB.called_at > datetime.utcnow() - timedelta(seconds=60),
        WaiterCallDB.answered_at == None
    ).first()

    if recent_call:
        raise HTTPException(status_code=429, detail="Already called waiter recently.")

    waiter_call = WaiterCallDB(
        restaurant_id=request.restaurant_id,
        table_id=request.table_id,
        called_at=datetime.utcnow()
    )
    db.add(waiter_call)
    db.commit()

    await send_telegram(
        f"🔔 <b>Call waiter / ເອີ້ນພະນັກງານ</b>\n"
        f"Table / ໂຕະ {table.number})"
    )

    return {
        "id": waiter_call.id,
        "status": "waiter_notified",
        "message": "Waiter is on the way! 🔔"
    }


@app.get("/api/call-status/{call_id}")
async def call_status(call_id: int, db: Session = Depends(get_db)):
    call = db.query(WaiterCallDB).filter(WaiterCallDB.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404)
    return {
        "id": call.id,
        "answered_at": call.answered_at.isoformat() if call.answered_at else None
    }


@app.get("/api/order-status/{order_id}")
async def order_status(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404)
    return {"id": order.id, "status": order.status.value}


# ─── API: Admin ───

@app.get("/api/admin/orders/{restaurant_id}")
async def admin_get_orders(restaurant_id: int, db: Session = Depends(get_db)):
    orders = db.query(OrderDB).options(
        joinedload(OrderDB.items).joinedload(OrderItemDB.dish).joinedload(
            DishDB.modifier_groups).joinedload(ModifierGroupDB.modifiers),
        joinedload(OrderDB.table)
    ).filter(
        OrderDB.restaurant_id == restaurant_id,
        OrderDB.status != OrderStatus.DONE
    ).order_by(OrderDB.created_at.desc()).limit(50).all()

    return [
        {
            "id": o.id,
            "status": o.status.value,
            "order_type": o.order_type.value,
            "total": o.total,
            "created_at": o.created_at.isoformat(),
            "table_number": o.table.number if o.table else "?",
            "items": [
                {
                    "dish_name": i.dish.name_en if i.dish else "?",
                    "qty": i.qty,
                    "mod": build_modifier_label(i, "en")
                }
                for i in o.items
            ]
        }
        for o in orders
    ]


@app.get("/api/admin/calls/{restaurant_id}")
async def admin_get_calls(restaurant_id: int, db: Session = Depends(get_db)):
    calls = db.query(WaiterCallDB).options(
        joinedload(WaiterCallDB.table)
    ).filter(
        WaiterCallDB.restaurant_id == restaurant_id,
        WaiterCallDB.answered_at == None
    ).order_by(WaiterCallDB.called_at.desc()).all()

    return [
        {
            "id": c.id,
            "table_number": c.table.number if c.table else "?",
            "called_at": c.called_at.isoformat(),
        }
        for c in calls
    ]


@app.get("/api/admin/analytics/{restaurant_id}")
async def admin_analytics_data(
        restaurant_id: int,
        days: int = 30,
        db: Session = Depends(get_db)
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    orders = db.query(OrderDB).options(
        joinedload(OrderDB.items).joinedload(OrderItemDB.dish)
    ).filter(
        OrderDB.restaurant_id == restaurant_id,
        OrderDB.created_at >= cutoff
    ).all()

    total_orders = len(orders)
    total_revenue = sum(o.total for o in orders)
    avg_check = total_revenue / total_orders if total_orders else 0
    completed = sum(1 for o in orders if o.status == OrderStatus.DONE)
    pending = sum(1 for o in orders if o.status in [
        OrderStatus.NEW, OrderStatus.ACCEPTED, OrderStatus.READY
    ])

    by_time = defaultdict(int)
    for o in orders:
        h = o.created_at.hour
        if 6 <= h < 11:
            by_time["morning"] += 1
        elif 11 <= h < 15:
            by_time["lunch"] += 1
        elif 15 <= h < 21:
            by_time["evening"] += 1
        else:
            by_time["night"] += 1

    dish_counts = defaultdict(int)
    for o in orders:
        for item in o.items:
            if item.dish:
                dish_counts[item.dish.name_en] += item.qty

    top_dishes = sorted(
        [{"name": k, "count": v} for k, v in dish_counts.items()],
        key=lambda x: x["count"], reverse=True
    )[:5]

    by_day = defaultdict(int)
    for o in orders:
        day = o.created_at.strftime("%Y-%m-%d")
        by_day[day] += o.total

    by_day_list = sorted(
        [{"date": k, "revenue": v} for k, v in by_day.items()],
        key=lambda x: x["date"]
    )

    return {
        "period_days": days,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_check": avg_check,
        "completed_orders": completed,
        "pending_orders": pending,
        "cancelled_orders": 0,
        "completed_percentage": (completed / total_orders * 100) if total_orders else 0,
        "by_time": dict(by_time),
        "top_dishes": top_dishes,
        "by_day": by_day_list,
    }


# ─── Admin Pages ───

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    restaurant = db.query(RestaurantDB).filter(RestaurantDB.id == 1).first()
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={"restaurant": restaurant}
    )


@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    restaurant = db.query(RestaurantDB).filter(RestaurantDB.id == 1).first()
    return templates.TemplateResponse(
        request=request,
        name="admin/analytics.html",
        context={"restaurant": restaurant}
    )


@app.get("/admin/menu", response_class=HTMLResponse)
async def admin_menu(db: Session = Depends(get_db)):
    return HTMLResponse(content="<h1>Admin Menu (TODO)</h1>")


# ─── Admin Actions ───

@app.post("/admin/order/{order_id}/status")
async def update_order_status(
        order_id: int,
        request: UpdateOrderStatusRequest,
        db: Session = Depends(get_db)
):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = request.status
    db.commit()
    return {"id": order.id, "status": order.status.value}


@app.post("/admin/order/{order_id}/cancel")
async def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"message": "Order cancelled"}


@app.post("/admin/call/{call_id}/answer")
async def answer_waiter_call(call_id: int, db: Session = Depends(get_db)):
    call = db.query(WaiterCallDB).filter(WaiterCallDB.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    call.answered_at = datetime.utcnow()
    db.commit()
    return {"id": call.id, "answered_at": call.answered_at.isoformat()}


@app.post("/admin/menu/toggle/{dish_id}")
async def toggle_dish_active(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(DishDB).filter(DishDB.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    dish.active = not dish.active
    db.commit()
    return {"id": dish.id, "active": dish.active, "status": "available" if dish.active else "86"}


# ─── Health ───

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/admin/qr/{restaurant_id}/{table_id}")
async def generate_qr(restaurant_id: int, table_id: int, request: Request):
    import qrcode, io
    from fastapi.responses import StreamingResponse
    url = f"{request.base_url}menu/{restaurant_id}/{table_id}"
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
