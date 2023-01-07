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
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT * FROM posted"
        cur.execute(s) # Execute the SQL
        list_users = cur.fetchall()
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'],list_users = list_users)
    # User is not loggedin redirect to login page
    return redirect(url_for('index'))
        
@app.route('/index/')
def index():
     return render_template('index.html')
 
@app.route('/storage', methods=['POST','GET'])
def storage():
    # Check if user is loggedin
    if 'loggedin' in session:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c = "SELECT * FROM images"
        cur.execute(c) # Execute the SQL
        all_display = cur.fetchall()
        # User is loggedin show them the home page
        return render_template('storage.html', username=session['username'],all_display = all_display)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET','POST'])
def profile(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        #photo_profile  = request.form['photo_profile']
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        display_image = cursor.fetchone()
        #image = cursor.fetchone(photo_profile)
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
        photo_profile  = request.form['photo_profile']
    
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
            cursor.execute("INSERT INTO users (fullname, username, password, email,photo_profile) VALUES (%s,%s,%s,%s,%s)", (fullname, username, _hashed_password, email,photo_profile))
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


@app.route("/upload",methods=["POST","GET"])
def upload_storage():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    now = datetime.now()
    print(now)
    if 'loggedin' in session:
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
        return redirect(url_for('storage'))
    return redirect(url_for('login'))

@app.route('/del_str/<string:id>', methods = ['POST','GET'])
def delete_str(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cur.execute('DELETE FROM images WHERE id = {0}'.format(id))
        conn.commit()
        flash('Post Removed Success')
        return redirect(url_for('storage'))
    return redirect(url_for('login'))


@app.route('/display/<filename>')
def display_image(filename):
    print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)





#============================================================Routing Dahsboard=================================================================
@app.route('/add_post', methods=['POST'])
def add_post():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        if request.method == 'POST':
         tit = request.form['tit']
         stit = request.form['stit']
         text = request.form['text']
         cur.execute("INSERT INTO posted (tit, stit, text) VALUES (%s,%s,%s)", (tit, stit, text))
         conn.commit()
         flash(' Added successfully')
         return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/edit/<id>', methods = ['POST', 'GET'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:

        cur.execute('SELECT * FROM posted WHERE id = %s', (id))
        data = cur.fetchall()
        cur.close()
        print(data[0])
        return render_template('edit.html', posted = data[0])
    return redirect(url_for('login'))
@app.route('/update/<id>', methods=['POST'])
def update_post(id):
    if 'loggedin' in session:

        if request.method == 'POST':
         tit = request.form['tit']
         stit = request.form['stit']
         text = request.form['text']
         
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE posted
            SET tit = %s,
                stit = %s,
                text = %s
            WHERE id = %s
        """, (tit, stit, text, id))
        flash('Editable Successfully')
        conn.commit()
        return redirect(url_for('home'))
    return redirect(url_for('login'))
@app.route('/delete/<string:id>', methods = ['POST','GET'])
def delete_post(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cur.execute('DELETE FROM posted WHERE id = {0}'.format(id))
        conn.commit()
        flash('Post Removed Success')
        return redirect(url_for('home'))
    return redirect(url_for('login'))


#======================================================================================================
@app.route('/chatroom', methods=['POST','GET'])
def chatroom():
    # Check if user is loggedin
    if 'loggedin' in session:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c = "SELECT * FROM account"
        cur.execute(c) # Execute the SQL
        chat_display = cur.fetchall()
        # User is loggedin show them the home page
        return render_template('chat_room.html', username=session['username'],chat_display = chat_display)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/add_chat', methods=['POST'])
def add_chat():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    now = datetime.now()
    if 'loggedin' in session:
         if request.method == 'POST':
            nickname = request.form['nickname']
            chat = request.form['chat']
            cur.execute("INSERT INTO account (nickname, chat, posted_on) VALUES (%s,%s,%s)", (nickname, chat, str(now)))
            conn.commit()
            print()
            cur.close()
            flash(' Added successfully')
            return redirect(url_for('chatroom'))
    return redirect(url_for('login'))

@app.route('/room')
def room():
    return render_template('room.html')

@app.route('/del_chat/<string:id>', methods = ['POST','GET'])
def delete_chat(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cur.execute('DELETE FROM account WHERE id = {0}'.format(id))
        conn.commit()
        flash('Post Removed Success')
        return redirect(url_for('chatroom'))
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)