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

# Neon ke liye tables verified/created
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search')
    highlighted_song = None
    
    if search_query:
        print(f"DEBUG: Searching for '{search_query}'")
        # 1. Database mein check karein
        highlighted_song = Song.query.filter(Song.title.ilike(f'%{search_query}%')).first()
        
        # 2. Agar DB mein nahi mila, toh Saavn API se fetch karein
        if not highlighted_song:
            try:
                api_url = f"https://saavn.dev/api/search/songs?query={search_query}"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', {}).get('results', [])
                    
                    if results:
                        top = results[0]
                        # Naya gaana object (Saavn se)
                        highlighted_song = Song(
                            title=top['name'], 
                            song_url=top['downloadUrl'][-1]['url'], 
                            thumbnail=top['image'][-1]['url']
                        )
                        db.session.add(highlighted_song)
                        db.session.commit()
                        db.session.remove() # Connection fresh rakhein
                        print(f"DEBUG: '{top['name']}' saved to Neon!")
                        
                        # ZAROORI: Refresh karein taaki dashboard update ho jaye
                        return redirect(url_for('index', search=search_query))
                    else:
                        print("DEBUG: API returned no results.")
            except Exception as e:
                db.session.rollback() # Error pe database rollback karein
                print(f"DEBUG ERROR: {str(e)}")

    # Dashboard logic: Saare gaane uthao
    all_songs = Song.query.all()
    
    if highlighted_song:
        # Search result ko sabse upar dikhao
        others = [s for s in all_songs if s.id != highlighted_song.id]
        random.shuffle(others)
        songs = [highlighted_song] + others
    else:
        # Normal dashboard
        songs = all_songs
        random.shuffle(songs)
    
    return render_template('index.html', songs=songs, search_query=search_query)

@app.route('/song/<int:id>')
def player(id):
    song = Song.query.get_or_404(id)
    return render_template('player.html', song=song)

# Admin delete route (Saavn gaano ke liye bhi kaam karega)
@app.route('/delete/<int:id>')
def delete_song(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    song = Song.query.get_or_404(id)
    db.session.delete(song)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
