import os
import random
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Song

app = Flask(__name__)

# --- CONNECTION STRING CHECK KARO ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_tSE5owdI4LzK@ep-quiet-wave-an83dt9u.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'moonlight_exclusive_2026'

db.init_app(app)

with app.app_context():
    db.create_all()
    print("🚀 SYSTEM START: Database tables verified!")

@app.route('/')
def index():
    search_query = request.args.get('search')
    highlighted_song = None
    
    # YE LINE LOGS MEIN DIKHNI CHAHIYE
    print(f"👉 LOG: Index page loaded. Search Query: {search_query}")
    
    if search_query:
        print(f"🔍 LOG: Searching for '{search_query}' in DB...")
        highlighted_song = Song.query.filter(Song.title.ilike(f'%{search_query}%')).first()
        
        if not highlighted_song:
            print(f"📡 LOG: Not in DB. Calling Saavn API for '{search_query}'...")
            try:
                api_url = f"https://saavn.dev/api/search/songs?query={search_query}"
                response = requests.get(api_url, timeout=10)
                print(f"📡 LOG: API Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', {}).get('results', [])
                    
                    if results:
                        top = results[0]
                        print(f"✅ LOG: Song Found! Saving '{top['name']}' to Neon...")
                        highlighted_song = Song(
                            title=top['name'], 
                            song_url=top['downloadUrl'][-1]['url'], 
                            thumbnail=top['image'][-1]['url']
                        )
                        db.session.add(highlighted_song)
                        db.session.commit()
                        print("💾 LOG: Successfully saved to Neon DB!")
                        # Refresh to show data
                        return redirect(url_for('index', search=search_query))
                    else:
                        print("❌ LOG: API returned no results.")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ LOG ERROR: {str(e)}")

    # Saare gaane uthao dashboard ke liye
    all_songs = Song.query.all()
    if highlighted_song:
        others = [s for s in all_songs if s.id != highlighted_song.id]
        random.shuffle(others)
        songs = [highlighted_song] + others
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
