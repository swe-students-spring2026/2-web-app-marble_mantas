from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from flask import Blueprint, request, render_template, redirect, url_for
from db import items, users
from bson import ObjectId

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")


def get_user_lists(user_id: str):
    list_names = []
    for item in items.find({"user_id": user_id, "status": "to_buy"}):
        list_name = (item.get("list") or "").strip() or "My List"
        if list_name not in list_names:
            list_names.append(list_name)
    return list_names


class User(UserMixin):
    def __init__(self, user_doc: dict):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]
        self.password = user_doc["password"]
        self.doc = user_doc

    @staticmethod
    def get_by_id(user_id: str):
        user_doc = users.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            return User(user_doc)
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


@auth_bp.route("/settings", methods=["GET"])
@login_required
def settings():
    return render_template("settings.html", username=current_user.username)


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
    return render_template("profile.html", username=current_user.username, lists=user_lists)
