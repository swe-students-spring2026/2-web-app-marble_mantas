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
    return jsonify([serialize_item(item) for item in items.find()]), 200

@items_bp.get("/<item_id>")
def get_item(item_id):
    item = items.find_one({"_id": ObjectId(item_id)})
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(serialize_item(item)), 200

@items_bp.post("")
def create_item():
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