import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
import cloudinary
import cloudinary.uploader
from models import db, Song
from functools import wraps # Ye zaroori hai login guard ke liye

app = Flask(__name__)

# --- CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'moonlight.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'moonlight_exclusive_2026'

db.init_app(app)

# ADMIN CREDENTIALS
ADMIN_USER = "anish"
ADMIN_PASS = "moonlight2026"

# CLOUDINARY CONFIG
cloudinary.config( 
  cloud_name = "dy3phvpmd", 
  api_key = "337268783782577", 
  api_secret = "6mnFXvTUglloLODp_OpoGJ0P3Q0" 
)

# --- LOGIN GUARD DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login')) # Login nahi hai toh login page pe bhejo
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash("Galat Password!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        songs = Song.query.filter(Song.title.ilike(f'%{search_query}%')).all()
    else:
        songs_list = Song.query.all()
        random.shuffle(songs_list)
        songs = songs_list
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/upload', methods=['GET', 'POST'])
@login_required # Ab ye login mangega!
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        title = request.form.get('title')
        if file and title:
            upload_result = cloudinary.uploader.upload(file, resource_type="video", folder="moonlight_mashups")
            new_song = Song(title=title, song_url=upload_result['secure_url'])
            db.session.add(new_song)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/delete/<int:id>')
@login_required # Sirf admin delete kar payega
def delete_song(id):
    song = Song.query.get_or_404(id)
    try:
        # Cloudinary se delete karna
        public_id = "moonlight_mashups/" + song.song_url.split('/')[-1].split('.')[0]
        cloudinary.uploader.destroy(public_id, resource_type="video")
    except:
        pass
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

if __name__ == '__main__':
    with app.app_context():
        # Instance folder banane ke liye
        if not os.path.exists('instance'):
            os.makedirs('instance')
        db.create_all()
    app.run(debug=True)
