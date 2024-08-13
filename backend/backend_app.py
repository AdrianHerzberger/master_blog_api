import secrets
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    decode_token,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_swagger_ui import get_swaggerui_blueprint
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Masterblog API"}
)

app = Flask(__name__)
CORS(app)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
app.config["JWT_SECRET_KEY"] = secrets.token_hex(16)
jwt = JWTManager(app)

users = {}

limiter = Limiter(
    get_remote_address, app=app, default_limits=["200 per day", "50 per hour"]
)


def load_posts_data():
    try:
        with open("static/posts_data.json") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print("Error: 'posts_data.json' file not found.")
        return []
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from 'posts_data.json'.")
        return []


POSTS = load_posts_data()

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"error": "User already exists"}), 400

    users[username] = generate_password_hash(password)
    return jsonify({"message": "User registered successfully"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    hashed_password = users.get(username)
    if not hashed_password or not check_password_hash(hashed_password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


def find_post_by_id(post_id):
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


@app.route("/api/posts", methods=["GET"])
@limiter.limit("10 per minute")
def get_posts():
    sort_field = request.args.get("sort")
    sort_direction = request.args.get("direction", "asc")

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    if sort_field and sort_field not in ["title", "content", "author", "date"]:
        return jsonify({"error": "Bad Request", "message": "Invalid sort field"}), 400

    if sort_direction not in ["asc", "desc"]:
        return jsonify({"error": "Bad Request", "message": "Invalid sort direction"}), 400

    sorted_posts = POSTS
    if sort_field:
        reverse = sort_direction == "desc"
        if sort_field == "date":
            sorted_posts = sorted(POSTS, key=lambda post: post[sort_field], reverse=reverse)
        else:
            sorted_posts = sorted(POSTS, key=lambda post: post[sort_field].lower(), reverse=reverse)

    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = sorted_posts[start:end]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": len(POSTS),
        "total_pages": (len(POSTS) + per_page - 1) // per_page,
        "posts": paginated_posts
    })



@app.route("/api/posts", methods=["POST"])
@jwt_required()
def add_post():
    data = request.json
    title = data.get("title")
    author = data.get("author")
    date = data.get("date")
    content = data.get("content")

    missing_fields = []
    if not title:
        missing_fields.append("title")
    if not content:
        missing_fields.append("content")
    if not author:
        missing_fields.append("author")
    if not date:
        missing_fields.append("date")

    if missing_fields:
        return jsonify({
            "error": "Bad Request",
            "message": f'Missing fields: {", ".join(missing_fields)}'
        }), 400

    post_id = len(POSTS) + 1

    new_post = {
        "id": post_id,
        "title": title,
        "author": author,
        "date": date,
        "content": content,
        "comments": []
    }

    POSTS.append(new_post)

    return jsonify(new_post), 201



@app.route("/api/posts/<int:id>", methods=["DELETE"])
def delete_post(id):
    post = find_post_by_id(id)
    if post is None:
        return "", 404

    POSTS.remove(post)

    return jsonify({"deleted": post, "message": "Post deleted successfully"})


@app.route("/api/posts/<int:id>", methods=["PUT"])
@jwt_required()
def update_post(id):
    post = find_post_by_id(id)
    if not post:
        return jsonify({"error": "Not Found", "message": "Post not found"}), 404

    data = request.json
    title = data.get("title")
    author = data.get("author")
    date = data.get("date")
    content = data.get("content")

    if not title and not content and not author and not date:
        return jsonify({"error": "Bad Request", "message": "No data provided to update"}), 400

    if title:
        post["title"] = title
    if author:
        post["author"] = author
    if date:
        post["date"] = date
    if content:
        post["content"] = content

    return jsonify(post), 200


@app.route("/api/posts/search", methods=["GET"])
def search_posts():
    title_query = request.args.get("title", "").lower()
    content_query = request.args.get("content", "").lower()
    author_query = request.args.get("author", "").lower()
    date_query = request.args.get("date", "").lower()

    filtered_posts = [
        post
        for post in POSTS
        if (title_query in post["title"].lower() if title_query else True)
        and (content_query in post["content"].lower() if content_query else True)
        and (author_query in post["author"].lower() if author_query else True)
        and (date_query in post["date"].lower() if date_query else True)
    ]

    return jsonify(filtered_posts)


@app.route("/api/posts/<int:id>/comments", methods=["POST"])
def add_comment(id):
    post = find_post_by_id(id)
    if not post:
        return jsonify({"error": "Not Found", "message": "Post not found"}), 404

    data = request.json
    comment = data.get("comment")

    if not comment:
        return jsonify({"error": "Bad Request", "message": "Comment is required"}), 400

    post["comments"].append(comment)
    return jsonify(post), 201


@app.route("/api/posts/<int:id>/like", methods=["POST"])
def like_post(id):
    post = find_post_by_id(id)
    if not post:
        return jsonify({"error": "Not Found", "message": "Post not found"}), 404

    if 'likes' not in post:
        post['likes'] = 0
    post['likes'] += 1

    return jsonify(post)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
