from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash
from datetime import datetime


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://mileage-trkr-py:eZOpGQdMq0rL8CZ3@localhost:8889/mileage-trkr-py'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "z1sdf234223ljwe2"


class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mileage_start = db.Column(db.Integer)
    mileage_end = db.Column(db.Integer)
    total_miles = db.Column(db.Integer)
    time_in = db.Column(db.DateTime)
    time_out = db.Column(db.DateTime)
    # TODO add a total time worked Column
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, mileage_start, owner, time_in=None):
        self.mileage_start = mileage_start
        if time_in is None:
            time_in = datetime.utcnow()
        self.time_in = time_in
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60))
    pw_hash = db.Column(db.String(120))
    days = db.relationship('Day', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/')

@app.route('/', methods=['GET','POST']) 
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = user.username
            flash("Logged in")
            return redirect('/clockin')
        elif not user:
            flash('That username does not exist, please retry or visit the signup page', 'error')
            return redirect('/login')
        elif not check_pw_hash(password, user.pw_hash):
            flash('Incorrect password', 'error')
            return render_template('login.html', username=username)

    return render_template('login.html')
        

@app.route("/clockin", methods=['GET', 'POST'])
def clock_in():
    if request.method == 'GET':
        if 'Day_ID' in session:
            return render_template('clockout.html', page_title='Enter your day end mileage')
        
        return render_template('clockin.html', page_title='Enter your beginning mileage')

    if 'username' not in session:
        flash('Error: Username not stored after login', 'error')
        return redirect('/')

    current_user = User.query.filter_by(username=session['username']).first()
    new_day = Day(request.form['mileage_start'], current_user) 
    db.session.add(new_day)
    db.session.commit()
    session['Day_ID'] = new_day.id
    flash('Successfully logged mileage')
    return render_template(clockout.html)

@app.route('/clockout', methods=['GET', 'POST'])
def clock_out():
    if request.method == 'GET':
        return render_template('clockout.html', page_title'Enter your day end mileage')

    mileage_end = request.form[mileage_end]
    current_day = Day.query.filter_by(id=session['Day_ID']).first()
    #TODO figure out how to calculate total worktime
    total_miles = mileage_end - current_day.mileage_start
    current_day.mileage_end = mileage_end
    current_day.total_miles = total_miles
    current_day.time_out = datetime.utcnow()
    del session['Day_ID']
    return render_template('clockin.html', page_title='Enter your beginning mileage')





@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        #returns welcome screen or shows any error messages
        
        username = request.form["username"]
        password = request.form["password"]
        password_retype = request.form["retype"]

        duplicate = User.query.filter_by(username=username).first()
    
        #run through potential errors
        if duplicate:
            error_name = 'That username already exists, please enter a new one'
            return render_template('signup.html', error_name=error_name)

        if username.strip() == "":
            error_name = "Please enter a Username"
            return render_template("signup.html", error_name=error_name)
    
        if len(username) < 3:
            error_name = "Please enter a Username with at least 3 characters"
            return render_template("signup.html", error_name=error_name)

        if password.strip() == "":
            error_name = "Please enter a Password"
            return render_template("signup.html", error_name=error_name, username=username)

        if password_retype.strip() == "":
            error_name = "Please retype your password"
            return render_template("signup.html", error_name=error_name, username=username)

        if password != password_retype:
            error_name = "Original password and retype do not match, please retype passwords"
            return render_template("signup.html", error_name=error_name, username=username)
        
        if len(password) < 3:
            error_name = "Please enter a password with a length of at least 3 characters"
            return render_template("signup.html", error_name=error_name, username=username)
        
        

        new_user = User(username, password)
        db.session.add(new_user)
        db.session.commit()

        session['username'] = username
        return redirect('/clockin')

    
    return render_template("signup.html")


@app.route('/logout')
def logout():
    del session['username']
    del session['Day_ID']
    return redirect('/')


if __name__ == '__main__':
    app.run()