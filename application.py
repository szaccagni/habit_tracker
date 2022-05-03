import os

from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from datetime import datetime
from PIL import ImageColor
from tempfile import mkdtemp
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError


app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mood.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    # Forget any user_id
    session.clear()
    return render_template("sign_in.html")
    

@app.route("/signin", methods=["POST"])
def signin():
    errors = []
    
    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
    
    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("pw")):
           errors.append('invalid username and/or password') 

    if len(errors) > 0: 
        return render_template("sign_in.html", errors=errors)
    else:
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/home")

    
@app.route("/home")
@login_required
def home():
    user = session.get("user_id")
    cur_month = datetime.now().month
    month_name = db.execute("SELECT name FROM calendar WHERE month = ? GROUP BY name", cur_month)[0]["name"]
    month_num = db.execute("SELECT month FROM calendar WHERE month = ? GROUP BY month", cur_month)[0]["month"]
    week1 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 1", cur_month)
    week2 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 2", cur_month)
    week3 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 3", cur_month)
    week4 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 4", cur_month)
    week5 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 5", cur_month)
    week6 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 6", cur_month)
    
    cur_month_formatted = "%,"+str(cur_month)+",%"
    habits = db.execute("SELECT * FROM habit WHERE user_id = ? AND active_for LIKE ?", user, cur_month_formatted)
    
    tracks_dict = db.execute("SELECT * FROM track WHERE user_id = ? AND done = 1", user)
    tracks = []
    for track in tracks_dict:
        tracks.append(str(track["date_id"])+str(track["habit_id"]))

    return render_template("layout.html", month_name=month_name, month_num=month_num, week1=week1, week2=week2,
    week3=week3, week4=week4, week5=week5, week6=week6, habits=habits, tracks=tracks)
    
    
@app.route("/habit_track", methods=["POST"])
@login_required
def h_track():
    user = session.get("user_id")
    habit = request.form.get("habit").upper()
    cur_month = datetime.now().month
    
    # check to see if this habit has been added before
    check = db.execute("SELECT * FROM habit WHERE name = ?", habit)
    if not check:
        active_for = ","
    else: 
        active_for = check[0]["active_for"]
    
    # create id to designate which months this habit is actively being tracked
    months_active = db.execute("SELECT * FROM calendar WHERE month >= ? GROUP BY month", cur_month)
    for row in months_active:
        active_for += str(row["month"])+","
    
    # add habit into database
    if not check:
        db.execute("INSERT INTO habit (user_id, name, active_for) VALUES(?, ?, ?)", user, habit, active_for)
    else:
        db.execute("UPDATE habit SET active_for = ? WHERE user_id = ? AND name = ?", active_for, user, habit)
    
    #reload page
    return redirect("/home")
        

@app.route("/habit_remove", methods=["POST"])
@login_required
def r_habit():
    user = session.get("user_id")
    habit = request.form.get("removal")
    active_id = db.execute("SELECT active_for FROM habit WHERE name = ?", habit)[0]["active_for"]
    cur_month = datetime.now().month
    months = db.execute("SELECT * FROM calendar WHERE month >= ? GROUP BY month", cur_month)
    remove_months = ""
    
    for row in months:
        remove_months += str(row["month"])+","
        
    active_id = active_id.replace(remove_months, "")
    
    # remove habit from active for future months
    db.execute("UPDATE habit SET active_for = ? WHERE user_id = ? AND name = ?", active_id, user, habit)
    
    #reload page
    return redirect("/home")


@app.route("/new_month",  methods=["POST"])
@login_required
def new_month():
    user = session.get("user_id")
    if request.form['new_month'] == 'backtrack':
        cur_month = int(request.form.get("month_num")) - 1
    elif request.form['new_month'] == 'forward':
        cur_month = int(request.form.get("month_num")) + 1
        
    month_name = db.execute("SELECT name FROM calendar WHERE month = ? GROUP BY name", cur_month)[0]["name"]
    month_num = db.execute("SELECT month FROM calendar WHERE month = ? GROUP BY month", cur_month)[0]["month"]
    week1 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 1", cur_month)
    week2 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 2", cur_month)
    week3 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 3", cur_month)
    week4 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 4", cur_month)
    week5 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 5", cur_month)
    week6 = db.execute("SELECT * FROM calendar WHERE month = ? AND week = 6", cur_month)

    cur_month_formatted = "%,"+str(cur_month)+",%"
    habits = db.execute("SELECT * FROM habit WHERE user_id = ? AND active_for LIKE ?", user, cur_month_formatted)
    
    tracks_dict = db.execute("SELECT * FROM track WHERE user_id = ? AND done = 1", user)
    tracks = []
    for track in tracks_dict:
        tracks.append(str(track["date_id"])+str(track["habit_id"]))
    
    return render_template("layout.html", month_name=month_name, month_num=month_num, week1=week1, week2=week2,
    week3=week3, week4=week4, week5=week5, week6=week6, habits=habits, tracks=tracks)


@app.route("/track", methods=["POST"])
@login_required
def track():
    user = session.get("user_id")
    habit_id = request.form.get("h_id")
    date_id = request.form.get("d_id")
    
    # check if a track already exists for this day for this habit
    check = db.execute("SELECT * FROM track WHERE habit_id = ? AND date_id = ? AND user_id = ?", 
                       habit_id, date_id, user)
    if not check:
        db.execute("INSERT INTO track (habit_id, date_id, done, user_id) VALUES(?, ?, 1, ?)", 
                   habit_id, date_id, user)
    else:
        db.execute("UPDATE track SET done = 1 WHERE id = ?", check[0]["id"])
    
    return redirect("/home")
    

@app.route("/un_track", methods=["POST"])
@login_required
def un_track():
    user = session.get("user_id")
    habit_id = request.form.get("h_id")
    date_id = request.form.get("d_id")

    db.execute("UPDATE track SET done = 0 WHERE habit_id = ? AND date_id = ? AND user_id = ?" , 
               habit_id, date_id, user)
    
    return redirect("/home")
    
@app.route("/logout", methods=["POST"])
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        errors = []
        username = request.form.get("username")
        pw = request.form.get("pw")
        confirm = request.form.get("confirm")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        
        if len(rows) == 1:
           errors.append("Username exists")
           
        if pw != confirm:
            errors.append("passwords do not match")
            
        if len(errors) > 0: 
            return render_template("register.html", errors=errors)
        else:
            # register user
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, 
            generate_password_hash(pw, method='pbkdf2:sha256', salt_length=8))
            return redirect("/home")
        
    else:
        return render_template("register.html")
        
    
@app.route("/test", methods=["POST"])
@login_required
def test():
    
    user = session.get("user_id")
    
    cur_month = datetime.now().month
    
    cur_month_formatted = "%,"+str(cur_month)+",%"
    habits = db.execute("SELECT * FROM habit WHERE user_id = ? AND active_for LIKE ?", user, cur_month_formatted)

    tracks_dict = db.execute("SELECT * FROM track WHERE user_id = ? AND done = 1", user)


    return render_template("test.html", test=tracks_dict)
    
