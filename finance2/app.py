import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    transaction_db = db.execute("SELECT symbol, SUM(shares) AS shares, price FROM `transaction` WHERE user_id = (?) GROUP BY symbol HAVING shares > 0;", user_id)
    money_db = db.execute("SELECT cash FROM users WHERE id = (?)", user_id)
    try:
        cash = money_db[0]["cash"]
    except:
        return redirect("/login")
    # Use lookup API to get the current price for each stock
    transaction_db = [dict(x, **{'price': lookup(x['symbol'])['price']}) for x in transaction_db]

    # Calcuate total price for each stock
    transaction_db = [dict(x, **{'total': x['price']*x['shares']}) for x in transaction_db]

    totals = cash + sum([x['total'] for x in transaction_db])


    return render_template("index.html", db = transaction_db, cash = cash, total = totals)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        price = request.form.get("price")
        try:
            price = int(price)
        except:
            return apology("INVALID shares")
    if price <= 0 or price == None:
        return apology("Value must be more than zero!")
    price = -price
    user_id = session["user_id"]
    money_database = db.execute("SELECT cash FROM users WHERE id = (?)", user_id)
    actual_money = money_database[0]["cash"]
    if actual_money >= -price:
        balance = actual_money + price
        time = datetime.datetime.now()
        db.execute("INSERT INTO `transaction` (user_id, price, date, note) VALUES (?, ?, ?, ?)", user_id, price, time, request.form.get("note"))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, user_id)
        flash("you now have $")
        flash(balance)

    else:
        return apology("you're too poor sorry")
    return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transaction = db.execute("SELECT * FROM `transaction` WHERE user_id = (?)", session["user_id"])
    return render_template("history.html", transactions=transaction)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        user = request.form.get("username")
        pw = request.form.get("password")
        conf = request.form.get("confirmation")
        if not user:
            return apology("I'm sorry but you have no name?")
        elif not pw:
            return apology("too lazy to give password?")
        elif not pw == conf:
            return apology("You have 2 password?")
        elif not len(pw) > 7:
            return apology("You need at least 8 character in the password!")
        hashed_pw = generate_password_hash(pw)
        try:
            add_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", user, hashed_pw)
            session["user_id"] = add_user
            return redirect("/")
        except:
            return apology("Sadly the username already exist.")




@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """sell shares of stock"""
    if request.method == "GET":
        return render_template("sell.html")
    else:
        price = int(request.form.get("price"))
    if price <= 0 or price == None:
        return apology("Value must be more than zero!")
    user_id = session["user_id"]
    money_database = db.execute("SELECT cash FROM users WHERE id = (?)", user_id)
    actual_money = money_database[0]["cash"]
    balance = actual_money + price
    time = datetime.datetime.now()
    db.execute("INSERT INTO `transaction` (user_id, price, date, note) VALUES (?, ?, ?, ?)", user_id, price, time, request.form.get("note"))
    db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, user_id)
    flash("you now have $")
    flash(balance)
    return redirect("/")