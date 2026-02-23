from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from db import items

items_bp = Blueprint("items_bp", __name__, url_prefix="/api/items")


def serialize_item(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "quantity": doc.get("quantity"),
        "status": doc.get("status"),
        "category": doc.get("category"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@items_bp.get("")
def list_items():
    #function to list all items
    return jsonify([serialize_item(item) for item in items.find()]), 200

@items_bp.get("/<item_id>")
def get_item(item_id):
    #function to get item by item_id
    item = items.find_one({"_id": ObjectId(item_id)})
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(serialize_item(item)), 200

@items_bp.post("")
def create_item():
    # function to create item
    data = request.get_json()

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    item = {
        "name": data.get("name"),
        "quantity": data.get("quantity", 1),
        "status": data.get("status", "to_buy"), #to_buy / pantry
        "category": data.get("category"),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    result = items.insert_one(item)
    item["_id"] = result.inserted_id
    return jsonify(serialize_item(item)), 201

@items_bp.put("/<item_id>")
def update_item(item_id):
    #function to update item
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    
    updates = {}
    if "name" in data: //required field, must not be empty
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400
        updates["name"] = name

    if "quantity" in data:
        updates["quantity"] = data.get("quantity")
    
    if "status" in data:
        updates["status"] = data.get("status")

    if "category" in data:
        updates["category"] = data.get("category")

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    updates["updated_at"] = datetime.now()
    result = items.update_one({"_id": ObjectId(item_id)}, {"$set": updates})
    if result.matched_count == 0:
        return jsonify({"error": "Item not found"}), 404
    
    item = items.find_one({"_id": ObjectId(item_id)})
    return jsonify(serialize_item(item)), 200

@items_bp.delete("/<item_id>")
def delete_item(item_id):
    #function to delete item
    result = items.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Item deleted"}), 200