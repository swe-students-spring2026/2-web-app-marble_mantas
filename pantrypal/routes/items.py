from flask import Blueprint, request, render_template, redirect, url_for
from bson import ObjectId
from datetime import datetime
from db import items
from flask_login import login_required

items_bp = Blueprint("items_bp", __name__, url_prefix="/items")


def serialize_item(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "quantity": doc.get("quantity"),
        "status": doc.get("status"),  # to_buy or pantry
        "category": doc.get("category"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@items_bp.get("")
@login_required
def list_items():
    pantry_items = [serialize_item(item) for item in items.find({"status": "pantry"})]
    shopping_items = [serialize_item(item) for item in items.find({"status": "to_buy"})]
    return render_template("items_list.html", pantry_items=pantry_items, shopping_items=shopping_items)

@items_bp.get("/pantry")
@login_required
def pantry_list():
    pantry_items = [serialize_item(item) for item in items.find({"status": "pantry"})]
    return render_template("pantry_list.html", items=pantry_items)

@items_bp.get("/shopping")
@login_required
def shopping_list():
    shopping_items = [serialize_item(item) for item in items.find({"status": "to_buy"})]
    return render_template("shopping_list.html", items=shopping_items)

@items_bp.get("/create")
@login_required
def create_item_form():
    return render_template("items_form.html", item=None, error=None)

@items_bp.post("")
@login_required
def create_item():
    name = (request.form.get("name") or "").strip()
    if not name:
        return render_template("items_form.html", item=None, error="Name is required")

    quantity = int(request.form.get("quantity", 1))
    if quantity <= 0:
        return render_template("items_form.html", item=None, error="Quantity must be at least 1")

    item_doc = {
        "name": name,
        "quantity": quantity,
        "status": request.form.get("status", "to_buy"),
        "category": request.form.get("category", ""),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    items.insert_one(item_doc)
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
    name = (request.form.get("name") or "").strip()
    if not name:
        return render_template("items_form.html", item=None, error="Name cannot be empty")

    quantity = int(request.form.get("quantity", 1))
    
    # Delete item if quantity is 0
    if quantity <= 0:
        items.delete_one({"_id": ObjectId(item_id)})
        return redirect(url_for("items_bp.list_items"))
    
    updates = {
        "name": name,
        "quantity": quantity,
        "status": request.form.get("status", "to_buy"),
        "category": request.form.get("category", ""),
        "updated_at": datetime.now(),
    }
    result = items.update_one({"_id": ObjectId(item_id)}, {"$set": updates})
    if result.matched_count == 0:
        return render_template("items_form.html", item=None, error="Item not found"), 404
    
    return redirect(url_for("items_bp.list_items"))

@items_bp.post("/<item_id>/delete")
@login_required
def delete_item(item_id):
    items.delete_one({"_id": ObjectId(item_id)})
    return redirect(url_for("items_bp.list_items"))
