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
    allowed_routes = ['login', 'signup', 'list_blogs', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route("/blog")
def list_blogs():
    
    blog_id = request.args.get("id")
    user_id = request.args.get("user")
    
    
    if blog_id != None:
        blog_item = Blog.query.filter_by(id=blog_id).first()
        return render_template("entry.html", blog=blog_item, author=blog_item.owner.username, page_title=blog_item.title+' by '+blog_item.owner.username)

    if user_id != None:
        blogs = Blog.query.filter_by(owner_id=user_id).all()
        author = User.query.filter_by(id=user_id).first()
        return render_template('author.html', page_title='Blogs by ' + author.username, blogs=blogs)

    posts = Blog.query.all()
    return render_template("listblogs.html", page_title="Blogs by all users", posts=posts)

@app.route('/')
def index():
        
    users = User.query.all()
    return render_template('index.html', page_title='Pick a user to see their blog', users=users  )


@app.route("/newday", methods=['GET', 'POST'])
def create_new():
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        if blog_title == "" or blog_body == "":
            flash("Please fill in both Title and Post fields", "error")
            return render_template('newpost.html', page_title="Add a blog entry", title=blog_title, body=blog_body)
        #TODO ADD OWNER PARAMETER TO NEW POST CONSTRUCTOR BELOW
        
        owner = User.query.filter_by(username=session['username']).first()
        new_post = Blog(blog_title, blog_body, owner)
        db.session.add(new_post)
        db.session.commit()
        blog_id=new_post.id
        return redirect("/blog?id="+str(blog_id))
        #return render_template("index.html", page_title="Build a Blog", posts=posts)
    
    return render_template("clockin.html", page_title="Enter your beginning mileage")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] 
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = user.username
            flash("Logged in")
            return redirect('/newpost')
        elif not user:
            flash('That username does not exist, please retry or visit the signup page', 'error')
            return redirect('/login')
        elif not check_pw_hash(password, user.pw_hash):
            flash('Incorrect password', 'error')
            return render_template('login.html', username=username)

    return render_template('login.html')



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
        return redirect('/newday')

    
    return render_template("signup.html")


@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


if __name__ == '__main__':
    app.run()