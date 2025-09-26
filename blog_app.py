import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    posts = db.relationship("BlogPost", backref="author", lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route("/")
def index():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("register"))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Email already registered!")
            return redirect(url_for("register"))

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully!")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect(url_for("index"))


@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        post = BlogPost(title=title, content=content, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()

        flash("Post created successfully!")
        return redirect(url_for("index"))

    return render_template("create_post.html")


@app.route("/post/<int:post_id>")
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template("view_post.html", post=post)


@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # Check if current user is the author
    if post.author != current_user:
        flash("You can only edit your own posts!")
        return redirect(url_for("index"))

    if request.method == "POST":
        post.title = request.form.get("title")
        post.content = request.form.get("content")
        post.updated_at = datetime.utcnow()
        db.session.commit()

        flash("Post updated successfully!")
        return redirect(url_for("view_post", post_id=post.id))

    return render_template("edit_post.html", post=post)


@app.route("/delete_post/<int:post_id>")
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    # Check if current user is the author
    if post.author != current_user:
        flash("You can only delete your own posts!")
        return redirect(url_for("index"))

    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully!")
    return redirect(url_for("index"))


@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        BlogPost.query.filter_by(user_id=user.id)
        .order_by(BlogPost.created_at.desc())
        .all()
    )
    return render_template("profile.html", user=user, posts=posts)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
