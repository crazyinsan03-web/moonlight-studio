import os
import random
import requests
import re
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Song

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_tSE5owdI4LzK@ep-quiet-wave-an83dt9u.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'moonlight_exclusive_2026'

db.init_app(app)

# --- DATABASE RESET & SYNC ---
with app.app_context():
    # Pehle purani table udayega (sirf ek baar reset ke liye)
    # Jab site chal jaye, toh line 21 ko delete kar dena
    db.drop_all() 
    db.create_all()
    print("🚀 Database Reset Successful! Nayi table ban gayi hai.")

# YouTube Link se ID nikalne ka function
def get_video_id(url):
    pattern = r"(?:v=|\/|embed\/|youtu.be\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        # User ke search ke hisaab se saved gaane dhoondo
        songs = Song.query.filter(Song.title.ilike(f'%{search_query}%')).all()
    else:
        # Dashboard par saare gaane shuffle karke dikhao
        songs = Song.query.all()
        random.shuffle(songs)
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        yt_link = request.form.get('youtube_link')
        v_id = get_video_id(yt_link)
        
        if v_id:
            try:
                # YouTube se automatic Title fetch karna
                response = requests.get(f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={v_id}")
                data = response.json()
                title = data.get('title', 'Moonlight Studio Mix')
                
                # Thumbnail high quality link
                thumb = f"https://img.youtube.com/vi/{v_id}/maxresdefault.jpg"
                
                # Neon Database mein save
                new_song = Song(title=title, video_id=v_id, thumbnail=thumb)
                db.session.add(new_song)
                db.session.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                print(f"Upload Error: {e}")
                
    return render_template('upload.html')

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

if __name__ == '__main__':
    app.run(debug=True)
