import os
import requests

from flask import Flask, session, redirect, url_for, render_template, request,flash, get_flashed_messages,jsonify
from flask_session import Session
# from flask_login import login_required

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"]      = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
# 'Scoped session' ensures that different users' interactions with the db are kept separate
db = scoped_session(sessionmaker(bind = engine))

@app.route('/')
def index():
    if not session.get("logged_in"):
        return render_template("index.html")
    else:
        return render_template("welcome.html", username = session["user_name"])

@app.route("/welcome")
def welcome():
    if not session.get("logged_in"):
        # retunr index
        return render_template("index.html")
    else:
        # if logged in go to welcome
        return render_template("welcome.html", username = session["user_name"])

@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    # session.clear()]
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in", category = 'error')
            return redirect(url_for('index'))
        else:
            return render_template("register.html")
    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        username     = request.form.get("username")
        password     = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            flash("Please provide a username", category = 'error')
            # return redirect(url_for('register'))

        # Query database for username
        user_check = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        # Check if username already exist
        if user_check:
            flash("Username already exist, please enter a new username", category = 'error')
            return redirect(url_for('register'))

        # Ensure password was submitted
        elif not password:
            flash("Please provide password", category = 'error')
            return redirect(url_for('register'))

        # Ensure confirmation wass submitted
        elif not confirmation:
            flash("Please confirm password", category = 'error')
            return redirect(url_for('register'))

        # Check if passwords match
        elif password != confirmation:
            flash("Passwords didn't match", category = 'error')
            return redirect(url_for('register'))

        # Hash user's password to store in DB
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Insert register into DB
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                            {"username":username,
                             "password":hash})

        # Commit changes to database
        db.commit()
        flash('Succes! Account created',category = 'success')

        # Redirect user to login page
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    # session.clear()
    if request.method == "GET":
        if session.get("logged_in"):
            flash("You are already logged in", category = 'error')
            return redirect(url_for('welcome'))
        else:
            return render_template("login.html")
    elif request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Please enter your username", category='error')
            return redirect(url_for('login'))
        elif not password :
             flash("Please enter your password", category = 'error')
             return redirect(url_for('login'))
        else:
        # Query user in database
            query_result = db.execute("SELECT id, password FROM users WHERE username LIKE :username", {"username": username}).fetchone()
            if not query_result:
                flash("User not registered. Please create an account", category = 'error')
                return redirect(url_for("login"))
            else:
                hash_result  = query_result.password
                user_id      = query_result.id

                if check_password_hash(hash_result, password):
                    session["logged_in"] = True
                    session["user_id"]   = user_id
                    session["user_name"] = username
                    return redirect(url_for('welcome'))
                else:
                    flash("Invalid password", category = 'error')
                    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session["logged_in"] = False
    session["user_id"]   = None
    return redirect(url_for('index'))

@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "GET":
        if not session.get("logged_in"):
            flash("Please log in to begin your search", category = 'error')
            return redirect(url_for('index'))
        else:
            return render_template("search.html", username = session["user_name"])
    elif request.method == "POST":
        session["books"] = []
        input = request.form.get('book')
        if not input:
            flash('Please enter a book name, author or ISBN', category = 'error')
            return redirect(url_for('search'))
        else:
            # message = ('')
            query_result = db.execute("SELECT * FROM books WHERE author iLIKE '%"+input+"%' OR title iLIKE '%"+input+"%' OR isbn iLIKE '%"+input+"%'").fetchall()
            for row in query_result:
                session['books'].append(row)
            message = (f'We found {len(session["books"])} results:')
            if len(session["books"]) == 0 :
                message = ('No matches found. Try again.')
            return render_template("search.html", data = session['books'], message = message)

@app.route('/book_info/<isbn>', methods = ['GET','POST'])
def book_info(isbn):
    if not session.get("logged_in"):
        flash("Please log in to access book information", category = 'error')
        return redirect(url_for('index'))
    else:
        username = session["user_name"]
        session["reviews"] = []

        # Book info
        book_data    = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
        # Other user's reviews
        book_reviews = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn",{"isbn":isbn}).fetchall()
        for row in book_reviews:
            session['reviews'].append(row)

        # Goodreads api
        res           = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "27HIkkHB3ixTMWYv9Xzyqg", "isbns": isbn})
        goodreads     = res.json()['books'][0] # res.json() returns a dictionary where the only key is 'books' and its value is a list of only one element(which is the actual dictionary with all theb book info)
        gr_count      = goodreads['work_ratings_count']
        gr_avg_rating = goodreads['average_rating']

        if request.method == "POST":
            # Add a review
            existing_review = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn AND user_username = :username",{"username":username,"isbn":isbn}).fetchone()
            if existing_review == None:
                new_review = request.form.get('text-review')
                rating     = request.form.get('stars-rating')
                db.execute("INSERT INTO reviews (book_isbn, rating, review, user_username,title,author) VALUES (:a,:b,:c,:d,:e,:f)",{"a":isbn,"b":rating,"c":new_review,"d":username,"e":book_data.title,"f":book_data.author })
                db.commit()
                flash('Your review has been saved!', category = 'success')
            elif existing_review != None:
                flash('You already submitted a review for this book', category = 'error')
    return render_template("book_info.html",book_data = book_data, reviews = session['reviews'],username = username,goodreads_count =gr_count, goodreads_rating=gr_avg_rating)
@app.route('/api/<isbn>', methods = ['GET'])
def api(isbn):
    # Make sure the isbn is in the db
    isbn_search = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
    if isbn_search is None:
      return jsonify({"error": "Invalid isbn"}), 422
    else:
        ratings      = db.execute("SELECT rating FROM reviews WHERE book_isbn = :isbn",{"isbn":isbn}).fetchall()
        review_count = db.execute("SELECT * FROM reviews WHERE book_isbn = :isbn",{"isbn":isbn}).rowcount
        # review_count = len(ratings)

        ratings_list = []
        for i in range(0,review_count):
            ratings_list.append(ratings[i].rating)

        ratings_avg =  sum(ratings_list)/review_count

        return jsonify({
          "title": isbn_search.title,
          "author": isbn_search.author,
          "year": isbn_search.year,
          "isbn": isbn,
          "review_count": review_count,
          "average_rating": ratings_avg
          })
@app.route('/profile', methods = ['GET'])
def profile():
    username = session["user_name"]
    reviews_list = db.execute("SELECT * FROM reviews WHERE user_username = :username",{"username":username}).fetchall()
    return render_template("profile.html",reviews_list = reviews_list)
