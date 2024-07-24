import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/get_reviews")
def get_reviews():
    reviews = list(mongo.db.reviews.find())
    return render_template("reviews.html", reviews=reviews)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("reviews.html", reviews=reviews)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # check if username is already in the db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user: 
            flash("Sorry, that Username is already in use!")
            return redirect(url_for("signup"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into the 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Sign Up Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed passowrd matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}!".format(
                        request.form.get("username")))
                    return redirect(
                        url_for("profile", username=session["user"]))
                    
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            #username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    # allows logged in user to change password
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        existing_user = mongo.db.users.find_one(
            {"username": session["user"]})

        if not existing_user or not check_password_hash(existing_user["password"], old_password):
            flash("Old Password is incorrect!", "error")
            print("here")
            return redirect(url_for("change_password"))
        print(old_password)
        print(new_password)
        print(confirm_password)
        if new_password != confirm_password:
            flash("Passwords don't match!", "error")
            return redirect(url_for("change_password"))

        hash_password = generate_password_hash(new_password)

        mongo.db.users.update_one(
            {"username": session["user"]}, {"$set": {"password": hash_password}})

        flash("Password had been update!", "success")

        return redirect(url_for("profile", username=session["user"]))

    return render_template("change_password.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if "user" in session:
        
        # grab the sessions user's username from the db
        username = mongo.db.users.find_one(
            {"username": session["user"]})["username"]

        # grab the list of reviews from the db
        reviews = list(mongo.db.reviews.find({"user_created": session["user"]}))

        return render_template("profile.html", username=username,  reviews=reviews)

    return redirect(url_for("login")) 


@app.route("/logout")
def logout():
    #remove user from session cookies
    flash("You have been logged out!")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        review = {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "genre": request.form.get("genre"),
            "rating": request.form.get("rating"),
            "summary": request.form.get("summary"),
            "cover_art": request.form.get("cover_art"),
            "user_created": session["user"],

        }
        mongo.db.reviews.insert_one(review)
        flash("Review has been successfully added!")
        return redirect(url_for("get_reviews"))

    return render_template("add_review.html")


@app.route("/edit_review<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        if session["user"] == "admin": 
            submit = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "genre": request.form.get("genre"),
                "rating": request.form.get("rating"),
                "summary": request.form.get("summary"),
                "cover_art": request.form.get("cover_art"),
                "affiliate_link": request.form.get("affiliate_link")
            }
        else:
            submit = {
                "title": request.form.get("title"),
                "author": request.form.get("author"),
                "genre": request.form.get("genre"),
                "rating": request.form.get("rating"),
                "summary": request.form.get("summary"),
                "cover_art": request.form.get("cover_art"),
            }
        mongo.db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": submit})
        flash("Review has been successfully updated!")

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("edit_review.html", review=review)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    flash("Review has been successfully deleted!")
    return redirect(url_for("get_reviews"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)