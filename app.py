import os
import random
import requests
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Song

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_tSE5owdI4LzK@ep-quiet-wave-an83dt9u.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'moonlight_exclusive_2026'

# Cloudinary Setup (Details match kar lena)
cloudinary.config( 
  cloud_name = "dr6v6vqun", 
  api_key = "142167139174154", 
  api_secret = "mE2M1t5P8fM681W1qM3f4NfNf6M" 
)

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search')
    highlighted_id = None
    
    if search_query:
        # 1. DB mein check
        song = Song.query.filter(Song.title.ilike(f'%{search_query}%')).first()
        
        if not song:
            try:
                # 2. Saavn API se dhoondo
                resp = requests.get(f"https://saavn.dev/api/search/songs?query={search_query}", timeout=15)
                if resp.status_code == 200:
                    results = resp.json().get('data', {}).get('results', [])
                    if results:
                        top = results[0]
                        # 3. Cloudinary par Upload (Permanent Storage)
                        upload = cloudinary.uploader.upload(top['downloadUrl'][-1]['url'], resource_type="video")
                        
                        # 4. Neon mein Save
                        song = Song(
                            title=top['name'],
                            song_url=upload['secure_url'],
                            thumbnail=top['image'][-1]['url']
                        )
                        db.session.add(song)
                        db.session.commit()
                        highlighted_id = song.id
            except Exception as e:
                db.session.rollback()
                print(f"Error: {e}")
        else:
            highlighted_id = song.id

    # Dashboard logic
    all_songs = Song.query.all()
    if highlighted_id:
        # Search wala gaana sabse upar
        s1 = [s for s in all_songs if s.id == highlighted_id]
        others = [s for s in all_songs if s.id != highlighted_id]
        random.shuffle(others)
        songs = s1 + others
    else:
        songs = all_songs
        random.shuffle(songs)
        
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

if __name__ == '__main__':
    app.run(debug=True)
