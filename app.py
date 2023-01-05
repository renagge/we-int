from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2  
import psycopg2.extras
import re 
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import urllib.request
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'kelompok4'
#=============================================DAATABASE=================================
DB_HOST = "localhost"
DB_NAME = "test"
DB_USER = "postgres"
DB_PASS = "170845"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

#===========================================================Routing Basic Layout=====================================================================   

@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
    
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('index'))
        
@app.route('/index/')
def index():
     return render_template('index.html')
 
@app.route('/storage')
def storage():
    if 'loggedin' in session:
    
        # User is loggedin show them the home page
        return render_template('storage.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))
  
@app.route('/profile', methods=['GET','POST'])
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#=================================================================ROUTING ACONT=============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
    
        _hashed_password = generate_password_hash(password)
 
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s,%s,%s,%s)", (fullname, username, _hashed_password, email))
            conn.commit()
            flash('You have successfully registered! \
                Please back to login menu')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('register.html')


 
@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        print(password)
 
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
 
        if account:
            password_rs = account['password']
            print(password_rs)
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')
 
    return render_template('login.html')


   
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

#==================================================================Routing Feature ============================================================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
   
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
   
def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload/',methods=["GET","POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    elif request.method == "POST":
        request.files.get("file")
        return redirect(url_for('home'))


@app.route("/upload",methods=["POST","GET"])
def upload_storage():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    now = datetime.now()
    print(now)
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        #print(files)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur.execute("INSERT INTO images (file_name, uploaded_on) VALUES (%s, %s)",[filename, now])
                conn.commit()
            print(file)
        cur.close()   
        flash('File(s) successfully uploaded')    
    return redirect('/storage')
@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


#============================================================Routing Dahsboard=================================================================
@app.route('/post',methods=['POST','POST'])
def post():
    if 'loggedin' in session:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if request.method == 'POST' and 'tittle_post' in request.form and 'body_post' in request.form and 'date_post' in request.form:
            tittle_post = request.form['tittle_post']
            body_post = request.form['body_post']
            date_post = request.form['date_post']
            cur.execute("INSERT INTO post (tittle_post,body_post,date_post) VALUES (%s,%s,%s)",(tittle_post,body_post,date_post))
            conn.commit()
            flash('Post Added successfully')
        return redirect(url_for('home'))
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/edit/<id>', methods = ['POST', 'GET'])
def get_post(id):
   cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   if 'loggedin' in session:
            cur.execute('SELECT * FROM post WHERE id = %s', (id))
            data = cur.fetchall()
            cur.close()
            print(data[0])
            return render_template('edit.html', post = data[0])
            return redirect(url_for('login'))

@app.route('/update/<id>', methods=['POST'])
def update_post(id):
    if 'loggedin' in session:
        if request.method == 'POST':
            tittle_post = request.form['tittle_post']
            body_post = request.form['body_post']
            date_post = request.form['date_post']
         
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE post
            SET tittle_post = %s,
                body_post = %s,
                date_post = %s
            WHERE id = %s
        """, (tittle_post, body_post, date_post, id))
        flash('Post Updated Successfully')
        conn.commit()
        return redirect(url_for('Index'))
    return redirect(url_for('login'))

@app.route('/delete/<string:id>', methods = ['POST','GET'])
def delete_student(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:  
        cur.execute('DELETE FROM post WHERE id = {0}'.format(id))
        conn.commit()
        flash('Post Removed Successfully')
        return redirect(url_for('Index'))
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)