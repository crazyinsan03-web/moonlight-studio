import psycopg2
from flask import Flask, render_template, request, jsonify, redirect, url_for
from youtubesearchpython import VideosSearch # Nayi Library

app = Flask(__name__)

# --- CONFIGURATION ---
DB_URL = "postgresql://neondb_owner:npg_M7CR8fwVjeNY@ep-blue-union-an1h5dmf-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- HTML ROUTES ---

@app.route('/')
def index():
    songs = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Home page par gaano ko randomly dikhao taaki refresh par naya content mile
        cur.execute('SELECT id, title, youtube_id, category FROM songs ORDER BY RANDOM()')
        songs = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    return render_template('index.html', songs=songs)

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Pehle Database (Neon) mein check karo
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE title ILIKE %s", (f'%{query}%',))
        db_results = cur.fetchall()

        if db_results:
            # Log Found: Agar mil gaya (Optional: search history ke liye)
            cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Found') ON CONFLICT DO NOTHING", (query,))
            conn.commit()
            cur.close()
            conn.close()
            return render_template('search_results.html', songs=db_results, source='db')

     else:
            # 2. YouTube "Research" mode
            videosSearch = VideosSearch(query, limit=5)
            yt_results = videosSearch.result()['result']
            
            # Log Not Found
            cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Not Found')", (query,))
            conn.commit()
            
            fallback_songs = []
            for video in yt_results:
                # IMPORTANT: Data ko List format mein dalo taaki template crash na ho
                # [0]: ID, [1]: Title, [2]: YouTube_ID, [3]: Category
                fallback_songs.append([
                    video['id'], 
                    video['title'], 
                    video['id'], 
                    'YouTube Global'
                ])
            
            cur.close()
            conn.close()
            return render_template('search_results.html', songs=fallback_songs, source='yt')
            
    except Exception as e:
        print(f"Search error: {e}")
        return redirect(url_for('index'))

@app.route('/player/<string:song_id>')
def player(song_id):
    # source='db' matlab Archive MP3, source='yt' matlab YouTube Iframe
    source = request.args.get('source', 'db')
    title_fallback = request.args.get('title', 'Moonlight Stream')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if source == 'db':
        # Database wala gaana: Fixed Order (id, title, yt_id, cat, audio_url)
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        
        # Next song logic (sirf DB gaano ke liye)
        cur.execute("SELECT id FROM songs WHERE id > %s LIMIT 1", (song_id,))
        next_res = cur.fetchone()
        next_id = next_res[0] if next_res else None
        
        cur.close()
        conn.close()
        
        if song:
            return render_template('player.html', song=song, next_id=next_id, source='db')
    else:
        # YouTube mode: No DB needed, seedha ID use hogi
        # Fake song object banaya taaki template crash na ho
        song = [song_id, title_fallback, song_id, 'YouTube Global', '']
        cur.close()
        conn.close()
        return render_template('player.html', song=song, next_id=None, source='yt')

    return "Song not found", 404

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        title = request.form.get('title')
        yt_id = request.form.get('link')
        audio_url = request.form.get('audio_url')
        category = request.form.get('category')
        
        cur.execute('''
            INSERT INTO songs (title, youtube_id, audio_url, category, is_mp3) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (title, yt_id, audio_url, category, True))
        conn.commit()
        return "<script>alert('Bhai, Gaana Add Ho Gaya!'); window.location.href='/admin';</script>"

    # Admin panel mein search logs bhi dikhao (Research wala feature)
    cur.execute('SELECT query_text, status, search_count, last_searched FROM search_logs ORDER BY last_searched DESC LIMIT 20')
    logs = cur.fetchall()

    cur.execute('SELECT * FROM songs ORDER BY id DESC')
    songs = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('admin.html', songs=songs, logs=logs)

# --- API ROUTES (USER SYSTEM) ---

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT phone FROM users WHERE phone = %s', (data.get('phone'),))
        if cur.fetchone():
            return jsonify({"status": "error", "message": "Number pehle se hai!"})
        
        cur.execute('INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)', 
                    (data.get('name'), data.get('phone'), data.get('password')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT name FROM users WHERE phone = %s AND password = %s', (data.get('phone'), data.get('password')))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            return jsonify({"status": "success", "user_name": user[0]})
        return jsonify({"status": "error", "message": "Galat details!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
