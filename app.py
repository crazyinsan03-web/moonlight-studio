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

# Neon ke liye tables banana
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search')
    
    if search_query:
        # Step 1: Pehle check karo kya database mein ye gaana hai?
        song_in_db = Song.query.filter(Song.title.ilike(f'%{search_query}%')).first()
        
        if not song_in_db:
            # Step 2: Agar nahi hai, toh JioSaavn API se fetch karo
            try:
                response = requests.get(f"https://saavn.dev/api/search/songs?query={search_query}")
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', {}).get('results', [])
                    
                    if results:
                        top = results[0] 
                        title = top['name']
                        url = top['downloadUrl'][-1]['url'] # Best quality
                        img = top['image'][-1]['url'] # Best image
                        
                        # Step 3: AUTO-SAVE to Neon
                        new_song = Song(title=title, song_url=url, thumbnail=img)
                        db.session.add(new_song)
                        db.session.commit()
            except Exception as e:
                print(f"Search Error: {e}")

    # Dashboard par saare saved gaane dikhao
    songs = Song.query.all()
    if songs:
        random.shuffle(songs)
    
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

if __name__ == '__main__':
    app.run(debug=True)
