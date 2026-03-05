from collections import OrderedDict
from datetime import datetime
from db import items
from flask import Blueprint, request, render_template, redirect, url_for, jsonify
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
        "list": doc.get("list"),
        "category": doc.get("category"),

        # Optional: Include timestamps if you want to show when items were added/updated
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def validate_and_parse_item(form):
    list_name = (form.get("list") or "").strip()
    if not list_name:
        return None, "List name is required"

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
        "list": list_name,
        "name": name,
        "quantity": qty,
        "status": status,
        "category": (form.get("category") or "").strip(),
        "updated_at": datetime.now()
    }, None


def get_user_items():
    return [serialize_item(item) for item in items.find({"user_id": current_user.id})]


def group_items_by_category(items):
    grouped = {}
    for item in items:
        cat = item.get("category") or "Uncategorized"
        grouped.setdefault(cat, []).append(item)

    sorted_categories = []
    for cat in sorted(grouped.keys()):
        sorted_items = sorted(grouped[cat], key=lambda x: (x.get("name") or "").lower())
        sorted_categories.append({"name": cat, "items": sorted_items})
    return sorted_categories

def group_items_by_list(item_docs, status=None):
    grouped = {}
    for item in item_docs:
        if status and item.get("status") != status:
            continue

        list_name = item.get("list") or "My List"
        category_name = item.get("category") or "Uncategorized"
        list_entry = grouped.setdefault(
            list_name,
            {"name": list_name, "categories": {}, "count": 0},
        )
        list_entry["count"] += 1
        list_entry["categories"].setdefault(category_name, []).append(item)

    lists = []
    for list_name in sorted(grouped.keys()):
        list_entry = grouped[list_name]
        
        sorted_categories = []
        for cat in sorted(list_entry["categories"].keys()):
            sorted_items = sorted(list_entry["categories"][cat], key=lambda x: (x.get("name") or "").lower())
            sorted_categories.append({"name": cat, "items": sorted_items})

        lists.append(
            {
                "name": list_entry["name"],
                "count": list_entry["count"],
                "categories": sorted_categories,
            }
        )
    return lists


def build_form_context(item=None, error=None):
    shopping_lists = group_items_by_list(get_user_items(), status="to_buy")
    existing_lists = [entry["name"] for entry in shopping_lists]
    existing_categories = []
    for entry in shopping_lists:
        for category in entry["categories"]:
            if category["name"] not in existing_categories:
                existing_categories.append(category["name"])

    return {
        "item": item,
        "error": error,
        "existing_lists": existing_lists,
        "existing_categories": existing_categories,
    }


@items_bp.get("")
@login_required
def list_items():
    return redirect(url_for('items_bp.pantry_list'))

@items_bp.get("/pantry")
@login_required
def pantry_list():
    search_term = (request.args.get("q") or "").strip()

    if search_term:
        pantry_items = item_search(search_term)  # Search through all lists if a search query is provided
    else:
        pantry_items = [item for item in get_user_items() if item["status"] == "pantry"]
        
    grouped_items = group_items_by_category(pantry_items)

    if request.args.get("format") == "json":
        return jsonify({"grouped_items": grouped_items})

    return render_template("pantry_list.html", grouped_items=grouped_items)

@items_bp.get("/shopping")
@login_required
def shopping_list():
    shopping_items = [item for item in get_user_items() if item["status"] == "to_buy"]
    grouped_items = group_items_by_list(shopping_items)
    return render_template("shopping_list.html", grouped_items=grouped_items)

@items_bp.get("/active")
@login_required
def active_list_page():
    shopping_lists = group_items_by_list(get_user_items(), status=None)
    selected_list_name = (request.args.get("list") or "").strip()
    active_list = None
    for entry in shopping_lists:
        if entry["name"] == selected_list_name:
            active_list = entry
            break
    # If the requested list was empty (no to_buy items), retain it as empty
    if active_list is None and selected_list_name:
        active_list = {"name": selected_list_name, "categories": [], "count": 0}
    # If no list specified, default to first list if it exists
    if active_list is None and shopping_lists:
        active_list = shopping_lists[0]
    return render_template("active_list.html", active_list=active_list)

@items_bp.get("/create")
@login_required
def create_item_form():
    return render_template("items_form.html", **build_form_context())

@items_bp.post("")
@login_required
def create_item():
    data, error = validate_and_parse_item(request.form)
    if error:
         return render_template("items_form.html", **build_form_context(item=request.form.to_dict(), error=error))
    data["user_id"] = current_user.id
    data["created_at"] = datetime.now()
    items.insert_one(data)
    if data["status"] == "pantry":
        return redirect(url_for("items_bp.pantry_list"))
    return redirect(url_for("items_bp.active_list_page", list=data["list"]))

@items_bp.get("/<item_id>/edit")
@login_required
def edit_item_form(item_id):
    item_doc = items.find_one({"_id": ObjectId(item_id), "user_id": current_user.id})
    if not item_doc:
        return render_template("items_form.html", **build_form_context(error="Item not found")), 404
    item = serialize_item(item_doc)
    return render_template("items_form.html", **build_form_context(item=item))

@items_bp.post("/<item_id>/update")
@login_required
def update_item(item_id):
    updates, error = validate_and_parse_item(request.form)
    if error:
        item_data = request.form.to_dict()
        item_data['id'] = item_id
        return render_template("items_form.html", **build_form_context(item=item_data, error=error))
    
    result = items.update_one(
        {"_id": ObjectId(item_id), "user_id": current_user.id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        return render_template("items_form.html", **build_form_context(error="Item not found or access denied")), 404
    
    cat_slug = updates.get("category", "").lower().replace(" ", "-")
    origin = request.form.get("origin")
    
    if origin == "active_list" or updates.get("status") != "pantry":
        return redirect(url_for("items_bp.active_list_page", list=updates["list"]) + f"#cat-{cat_slug}")
        
    return redirect(url_for("items_bp.pantry_list", open_cat=cat_slug) + f"#cat-{cat_slug}")

@items_bp.post("/<item_id>/delete")
@login_required
def delete_item(item_id):
    item_doc = items.find_one({"_id": ObjectId(item_id), "user_id": current_user.id})
    if not item_doc:
        return render_template("items_form.html", **build_form_context(error="Item not found or access denied")), 404

    result = items.delete_one({
        "_id": ObjectId(item_id), 
        "user_id": current_user.id
    })
    if result.deleted_count == 0:
        return render_template("items_form.html", **build_form_context(error="Item not found or access denied")), 404
    
    cat_slug = item_doc.get("category", "Uncategorized").lower().replace(" ", "-")
    
    if item_doc.get("status") == "pantry":
        return redirect(url_for("items_bp.pantry_list", open_cat=cat_slug) + f"#cat-{cat_slug}")
    return redirect(url_for("items_bp.active_list_page", list=item_doc.get("list") or "My List") + f"#cat-{cat_slug}")


def item_search(search_term, status = None):
    cleaned_term = (search_term or "").strip()
    if not cleaned_term and not status:
        return []  # Return nothing if no search term or status filter provided
    
    query = {
        "user_id": current_user.id, 
        "name": {"$regex": cleaned_term, "$options": "i"}
    }
    
    if status in ALLOWED_STATUSES:
        query["status"] = status

    return [serialize_item(item) for item in items.find(query)]
