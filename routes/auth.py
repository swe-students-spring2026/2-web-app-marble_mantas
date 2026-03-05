import base64
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from db import items, users
from bson import ObjectId

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")
MAX_PROFILE_IMAGE_BYTES = 4 * 1024 * 1024


def get_user_lists(user_id: str):
    list_names = []
    for item in items.find({"user_id": user_id, "status": "to_buy"}):
        list_name = (item.get("list") or "").strip() or "My List"
        if list_name not in list_names:
            list_names.append(list_name)
    return list_names


class User:
    def __init__(self, user_doc: dict):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]
        self.password = user_doc["password"]
        self.doc = user_doc

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    @staticmethod
    def get_by_id(user_id: str):
        try:
            user_doc = users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return User(user_doc)
        except Exception:
            pass
        return None

    @staticmethod
    def get_by_username(username: str):
        user_doc = users.find_one({"username": username})
        if user_doc:
            return User(user_doc)
        return None

    @staticmethod
    def create(username: str, password: str):
        if users.find_one({"username": username}):
            return None  # Username already exists
        user_doc = {"username": username, "password": password}
        result = users.insert_one(user_doc)
        return User(users.find_one({"_id": result.inserted_id}))

    @staticmethod
    def verify_credentials(username: str, password: str):
        user_doc = users.find_one({"username": username, "password": password})
        if user_doc:
            return User(user_doc)
        return None


def encode_profile_image(uploaded_file):
    if not uploaded_file or not uploaded_file.filename:
        return None, None

    mimetype = (uploaded_file.mimetype or "").lower()
    if not mimetype.startswith("image/"):
        return None, "Profile picture must be an image file."

    raw_bytes = uploaded_file.read()
    if not raw_bytes:
        return None, "Selected image is empty."
    if len(raw_bytes) > MAX_PROFILE_IMAGE_BYTES:
        return None, "Profile picture must be 4 MB or smaller."

    encoded = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mimetype};base64,{encoded}", None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            error = "Username and password are required"
        elif len(password) < 6:
            error = "Password must be at least 6 characters long"
        else:
            user = User.create(username, password)
            if not user:
                error = "Username already exists"
            else:
                login_user(user)
                return redirect(url_for("auth_bp.home"))
    return render_template("register.html", error=error)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            error = "Username and password are required"
        else:
            user = User.verify_credentials(username, password)
            if not user:
                error = "Invalid username or password"
            else:
                login_user(user)
                return redirect(url_for("auth_bp.home"))
    return render_template("login.html", error=error)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth_bp.login"))


@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    active_name = (request.args.get("active") or "").strip() or None
    user_doc = users.find_one({"_id": ObjectId(current_user.id)}) or {}
    error = None
    success = None
    photo_added = False

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        current_username = str(user_doc.get("username") or current_user.username or "").strip()
        current_password = str(user_doc.get("password") or current_user.password or "")

        requested_username = (request.form.get("username") or "").strip()
        current_password_input = request.form.get("password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        updates = {}

        if request.form.get("username") is not None:
            if not requested_username:
                error = "Username is required."
            elif requested_username != current_username:
                duplicate = users.find_one({
                    "username": requested_username,
                    "_id": {"$ne": ObjectId(current_user.id)},
                })
                if duplicate:
                    error = "Username already exists."
                else:
                    updates["username"] = requested_username

        wants_password_change = any([current_password_input, new_password, confirm_password])
        if not error and wants_password_change:
            if not current_password_input:
                error = "Enter your current password."
            elif current_password_input != current_password:
                error = "Current password is incorrect."
            elif len(new_password) < 6:
                error = "New password must be at least 6 characters long."
            elif new_password != confirm_password:
                error = "New password and confirm password must match."
            elif new_password == current_password:
                error = "New password must be different from current password."
            else:
                updates["password"] = new_password

        profile_image_data, image_error = encode_profile_image(request.files.get("profile_photo"))
        if not error and image_error:
            error = image_error
        elif profile_image_data:
            updates["profile_image"] = profile_image_data
            photo_added = True

        if error:
            if is_ajax:
                return jsonify({"ok": False, "error": error}), 400
        elif updates:
            users.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": updates},
            )
            refreshed_user = User.get_by_id(current_user.id)
            if refreshed_user:
                login_user(refreshed_user)
                user_doc = refreshed_user.doc
            success = "Settings saved."
            if is_ajax:
                return jsonify(
                    {
                        "ok": True,
                        "message": success,
                        "profile_image": str(user_doc.get("profile_image") or ""),
                    }
                )
        else:
            success = "No changes to save."
            if is_ajax:
                return jsonify({"ok": True, "message": success})

    return render_template(
        "settings.html",
        username=str(user_doc.get("username") or current_user.username),
        profile_image=str(user_doc.get("profile_image") or ""),
        error=error,
        success=success,
        photo_added=photo_added,
        active_name=active_name,
    )


@auth_bp.route("/home", methods=["GET"])
@login_required
def home():
    user_lists = get_user_lists(current_user.id)
    active_list_name = user_lists[0] if user_lists else None
    return render_template("home.html", active_list_name=active_list_name)


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    user_lists = get_user_lists(current_user.id)
    profile_image = str((current_user.doc or {}).get("profile_image") or "")
    return render_template(
        "profile.html",
        username=current_user.username,
        lists=user_lists,
        profile_image=profile_image,
    )
