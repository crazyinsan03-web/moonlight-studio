import os
import random
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Song

app = Flask(__name__)

# --- CONFIGURATION (NEON LINK SET) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_tSE5owdI4LzK@ep-quiet-wave-an83dt9u.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'moonlight_exclusive_2026'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search')
    highlighted_song = None
    
    if search_query:
        # 1. Database mein dhoondo
        highlighted_song = Song.query.filter(Song.title.ilike(f'%{search_query}%')).first()
        
        # 2. Agar nahi hai toh Saavn API se uthao
        if not highlighted_song:
            try:
                response = requests.get(f"https://saavn.dev/api/search/songs?query={search_query}")
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', {}).get('results', [])
                    
                    if results:
                        top = results[0] 
                        # Naya gaana object banao
                        highlighted_song = Song(
                            title=top['name'], 
                            song_url=top['downloadUrl'][-1]['url'], 
                            thumbnail=top['image'][-1]['url']
                        )
                        db.session.add(highlighted_song)
                        db.session.commit()
            except Exception as e:
                print(f"Search Error: {e}")

    # Dashboard logic: Saare gaane uthao
    all_songs = Song.query.all()
    
    if highlighted_song:
        # Search result ko sabse upar rakhna hai
        others = [s for s in all_songs if s.id != highlighted_song.id]
        random.shuffle(others)
        songs = [highlighted_song] + others
    else:
        # Normal time pe sab shuffle
        songs = all_songs
        random.shuffle(songs)
    
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

if __name__ == '__main__':
    app.run(debug=True)
