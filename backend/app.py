from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///connectly.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# DATABASE MODELS
# =========================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    bio = db.Column(
        db.String(300),
        default="Hey! I am using Connectly."
    )

    profile_image = db.Column(
        db.String(500),
        default=""
    )


class Post(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="posts"
    )


class Comment(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    text = db.Column(
        db.String(500),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    user = db.relationship(
        "User"
    )


class Like(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "post_id",
            "user_id"
        ),
    )


class Follow(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    follower_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    following_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "follower_id",
            "following_id"
        ),
    )


# =========================
# HELPER FUNCTIONS
# =========================

def user_details(user, current_user_id=None):

    followers = Follow.query.filter_by(
        following_id=user.id
    ).count()

    following = Follow.query.filter_by(
        follower_id=user.id
    ).count()

    is_following = False

    if current_user_id:

        is_following = Follow.query.filter_by(
            follower_id=current_user_id,
            following_id=user.id
        ).first() is not None

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "profile_image": user.profile_image,
        "followers": followers,
        "following": following,
        "is_following": is_following
    }


def post_details(post, current_user_id=None):

    likes = Like.query.filter_by(
        post_id=post.id
    ).count()

    comments = Comment.query.filter_by(
        post_id=post.id
    ).all()

    liked_by_user = False

    if current_user_id:

        liked_by_user = Like.query.filter_by(
            post_id=post.id,
            user_id=current_user_id
        ).first() is not None

    comment_list = []

    for comment in comments:

        comment_list.append({
            "id": comment.id,
            "text": comment.text,
            "username": comment.user.username
        })

    return {
        "id": post.id,
        "content": post.content,
        "username": post.user.username,
        "user_id": post.user_id,
        "created_at": post.created_at.strftime(
            "%Y-%m-%d %H:%M"
        ),
        "likes": likes,
        "liked": liked_by_user,
        "comments": comment_list
    }


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return jsonify({
        "message": "Connectly API is running"
    })


# =========================
# REGISTER
# =========================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:

        return jsonify({
            "error": "All fields are required"
        }), 400

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:

        return jsonify({
            "error": "Username or email already exists"
        }), 409

    hashed_password = generate_password_hash(
        password
    )

    user = User(
        username=username,
        email=email,
        password=hashed_password
    )

    db.session.add(user)

    db.session.commit()

    return jsonify({
        "message": "Account created successfully",
        "user": user_details(user)
    }), 201


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if not check_password_hash(
        user.password,
        password
    ):

        return jsonify({
            "error": "Invalid username or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "user": user_details(user)
    })


# =========================
# GET ALL USERS
# =========================

@app.route(
    "/users",
    methods=["GET"]
)
def get_users():

    users = User.query.all()

    result = []

    for user in users:

        result.append(
            user_details(user)
        )

    return jsonify(result)


# =========================
# GET PROFILE
# =========================

@app.route(
    "/users/<int:user_id>",
    methods=["GET"]
)
def get_profile(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify(
        user_details(user)
    )


# =========================
# UPDATE PROFILE
# =========================

@app.route(
    "/users/<int:user_id>",
    methods=["PUT"]
)
def update_profile(user_id):

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json()

    user.bio = data.get(
        "bio",
        user.bio
    )

    user.profile_image = data.get(
        "profile_image",
        user.profile_image
    )

    db.session.commit()

    return jsonify({
        "message": "Profile updated",
        "user": user_details(user)
    })


# =========================
# CREATE POST
# =========================

@app.route(
    "/posts",
    methods=["POST"]
)
def create_post():

    data = request.get_json()

    content = data.get("content")
    user_id = data.get("user_id")

    if not content or not user_id:

        return jsonify({
            "error": "Post content and user ID are required"
        }), 400

    user = db.session.get(
        User,
        user_id
    )

    if not user:

        return jsonify({
            "error": "User not found"
        }), 404

    post = Post(
        content=content,
        user_id=user_id
    )

    db.session.add(post)

    db.session.commit()

    return jsonify(
        post_details(
            post,
            user_id
        )
    ), 201


# =========================
# GET POSTS
# =========================

@app.route(
    "/posts",
    methods=["GET"]
)
def get_posts():

    current_user_id = request.args.get(
        "user_id",
        type=int
    )

    posts = Post.query.order_by(
        Post.id.desc()
    ).all()

    result = []

    for post in posts:

        result.append(
            post_details(
                post,
                current_user_id
            )
        )

    return jsonify(result)


# =========================
# DELETE POST
# =========================

@app.route(
    "/posts/<int:post_id>",
    methods=["DELETE"]
)
def delete_post(post_id):

    post = db.session.get(
        Post,
        post_id
    )

    if not post:

        return jsonify({
            "error": "Post not found"
        }), 404

    Comment.query.filter_by(
        post_id=post.id
    ).delete()

    Like.query.filter_by(
        post_id=post.id
    ).delete()

    db.session.delete(post)

    db.session.commit()

    return jsonify({
        "message": "Post deleted successfully"
    })


# =========================
# LIKE / UNLIKE
# =========================

@app.route(
    "/posts/<int:post_id>/like",
    methods=["POST"]
)
def toggle_like(post_id):

    data = request.get_json()

    user_id = data.get("user_id")

    existing_like = Like.query.filter_by(
        post_id=post_id,
        user_id=user_id
    ).first()

    if existing_like:

        db.session.delete(
            existing_like
        )

        message = "Post unliked"

    else:

        new_like = Like(
            post_id=post_id,
            user_id=user_id
        )

        db.session.add(
            new_like
        )

        message = "Post liked"

    db.session.commit()

    likes = Like.query.filter_by(
        post_id=post_id
    ).count()

    return jsonify({
        "message": message,
        "likes": likes
    })


# =========================
# ADD COMMENT
# =========================

@app.route(
    "/posts/<int:post_id>/comments",
    methods=["POST"]
)
def add_comment(post_id):

    data = request.get_json()

    text = data.get("text")
    user_id = data.get("user_id")

    if not text:

        return jsonify({
            "error": "Comment cannot be empty"
        }), 400

    comment = Comment(
        text=text,
        post_id=post_id,
        user_id=user_id
    )

    db.session.add(comment)

    db.session.commit()

    return jsonify({
        "id": comment.id,
        "text": comment.text,
        "username": comment.user.username
    }), 201


# =========================
# FOLLOW / UNFOLLOW
# =========================

@app.route(
    "/users/<int:user_id>/follow",
    methods=["POST"]
)
def toggle_follow(user_id):

    data = request.get_json()

    follower_id = data.get(
        "follower_id"
    )

    if follower_id == user_id:

        return jsonify({
            "error": "You cannot follow yourself"
        }), 400

    existing_follow = Follow.query.filter_by(
        follower_id=follower_id,
        following_id=user_id
    ).first()

    if existing_follow:

        db.session.delete(
            existing_follow
        )

        message = "Unfollowed"

    else:

        new_follow = Follow(
            follower_id=follower_id,
            following_id=user_id
        )

        db.session.add(
            new_follow
        )

        message = "Following"

    db.session.commit()

    following_count = Follow.query.filter_by(
        follower_id=follower_id
    ).count()

    followers_count = Follow.query.filter_by(
        following_id=user_id
    ).count()

    return jsonify({
        "message": message,
        "following": following_count,
        "followers": followers_count
    })


# =========================
# CREATE DATABASE
# =========================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(
        debug=True
    )