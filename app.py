from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm

from sqlalchemy.exc import IntegrityError


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///authorize_exercise"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)
app.app_context().push()

toolbar = DebugToolbarExtension(app)

db.create_all()


@app.route("/")
def show_home_page():
    """Actually redirects to register"""
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def show_register():
    """Shows/ handles registration form"""
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username/Email taken")
            return render_template("register.html", form=form)
        session["username"] = new_user.username
        return redirect(f"/users/{new_user.username}")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def show_login_form():
    """log in"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username/password"]

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.pop("username")
    return redirect("/")


@app.route("/users/<username>")
def show_secret_page(username):
    if "username" in session:
        user = User.query.get_or_404(username)
        feedback = Feedback.query.filter(username == username)
        return render_template("username.html", user=user, feedback=feedback)
    return redirect("/login")


@app.route("/users/<username>/delete")
def show_delete_page(username):
    if "username" in session:
        user = User.query.get_or_404(username)
        return render_template("delete_page.html", user=user)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    if "username" in session:
        user = User.query.get_or_404(username)
        db.session.delete(user)
        db.session.commit()
        session.pop("username")
        return redirect("/")


@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback_form(username):
    if "username" not in session:
        flash("This page is only available to subscribers. Please log in.", "danger")
        return redirect("/")

    form = FeedbackForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(username)
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(
            title=title, content=content, username=session["username"]
        )
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f"/users/{user.username}")
    return render_template("feedback.html", form=form)
