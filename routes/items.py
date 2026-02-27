from datetime import datetime
from db import items
from flask import Blueprint, request, render_template, redirect, url_for
from bson import ObjectId
from flask_login import login_required, current_user

items_bp = Blueprint("items_bp", __name__, url_prefix="/items")
ALLOWED_STATUSES = {"to_buy", "pantry"}

# ensure quantity is an integer and return None if invalid
def parse_quantity(value):
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return None
    return quantity

def serialize_item(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "quantity": doc.get("quantity"),
        "status": doc.get("status"),  # to_buy or pantry
        "category": doc.get("category"),

        # Optional: Include timestamps if you want to show when items were added/updated
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def validate_and_parse_item(form):
    name = (form.get("name") or "").strip()
    if not name:
        return None, "Name is required"
        
    try:
        qty = int(form.get("quantity", 1))
        if qty < 1: raise ValueError
    except (TypeError, ValueError):
        return None, "Quantity must be at least 1"
        
    status = form.get("status", "to_buy")
    if status not in ALLOWED_STATUSES:
        return None, "Invalid status"
        
    return {
        "name": name,
        "quantity": qty,
        "status": status,
        "category": form.get("category", ""),
        "updated_at": datetime.now()
    }, None


@items_bp.get("")
@login_required
def list_items():
    pantry_items = [serialize_item(item) for item in items.find({"status": "pantry", "user_id": current_user.id})]
    shopping_items = [serialize_item(item) for item in items.find({"status": "to_buy", "user_id": current_user.id})]
    return render_template("items_list.html", pantry_items=pantry_items, shopping_items=shopping_items)

@items_bp.get("/pantry")
@login_required
def pantry_list():
    pantry_items = [serialize_item(item) for item in items.find({"status": "pantry", "user_id": current_user.id})]
    return render_template("pantry_list.html", items=pantry_items)

@items_bp.get("/shopping")
@login_required
def shopping_list():
    shopping_items = [serialize_item(item) for item in items.find({"status": "to_buy", "user_id": current_user.id})]
    return render_template("shopping_list.html", items=shopping_items)

@items_bp.get("/active")
def active_list_page():
    demo_mode = request.args.get("demo") == "1"
    return render_template("active_list.html", demo_mode=demo_mode)

@items_bp.get("/create")
def create_item_form():
    demo_mode = request.args.get("demo") == "1"
    return render_template("items_form.html", item=None, error=None, demo_mode=demo_mode)

@items_bp.post("")
@login_required
def create_item():
    data, error = validate_and_parse_item(request.form)
    if error:
         return render_template("items_form.html", item=request.form, error=error)
    data["user_id"] = current_user.id
    data["created_at"] = datetime.now()
    items.insert_one(data)
    return redirect(url_for("items_bp.list_items"))

@items_bp.get("/<item_id>/edit")
@login_required
def edit_item_form(item_id):
    item_doc = items.find_one({"_id": ObjectId(item_id)})
    if not item_doc:
        return render_template("items_form.html", item=None, error="Item not found"), 404
    item = serialize_item(item_doc)
    return render_template("items_form.html", item=item, error=None)

@items_bp.post("/<item_id>/edit")
@login_required
def update_item(item_id):
    updates, error = validate_and_parse_item(request.form)
    if error:
        item_data = request.form.to_dict()
        item_data['id'] = item_id
        return render_template("items_form.html", item=item_data, error=error)
    
    result = items.update_one(
        {"_id": ObjectId(item_id), "user_id": current_user.id}, 
        {"$set": updates}
    )
    if result.matched_count == 0:
        return render_template("items_form.html", item=None, error="Item not found or access denied"), 404
    
    return redirect(url_for("items_bp.list_items"))

@items_bp.post("/<item_id>/delete")
@login_required
def delete_item(item_id):
    result = items.delete_one({
        "_id": ObjectId(item_id), 
        "user_id": current_user.id
    })
    # flash a message
    if result.deleted_count == 0:
        return render_template("items_list.html", error="Item not found or access denied"), 404
    return redirect(url_for("items_bp.list_items"))