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
        
        # 1. Pehle Database mein check karo
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE title ILIKE %s", (f'%{query}%',))
        db_results = cur.fetchall()

        if db_results:
            cur.close()
            conn.close()
            return render_template('search_results.html', songs=db_results, source='db')
        
        else:
            # 2. Agar DB mein nahi hai, toh YouTube Search (Research Mode)
            videosSearch = VideosSearch(query, limit=5)
            yt_results = videosSearch.result()['result']
            
            # Missing song ko log karo (search_logs table honi chahiye)
            try:
                cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Not Found')", (query,))
                conn.commit()
            except:
                conn.rollback() # Agar table nahi hai toh crash na ho
            
            fallback_songs = []
            for v in yt_results:
                # Format: [id, title, youtube_id, category]
                # Template ke compatibility ke liye list format mein data
                fallback_songs.append([v['id'], v['title'], v['id'], 'YouTube Global'])
            
            cur.close()
            conn.close()
            return render_template('search_results.html', songs=fallback_songs, source='yt')

    except Exception as e:
        print(f"Search error: {e}")
        return redirect(url_for('index'))

@app.route('/player/<string:song_id>')
def player(song_id):
    source = request.args.get('source', 'db')
    title_fb = request.args.get('title', 'Moonlight Stream') # YouTube fallback ke liye
    
    conn = get_db_connection()
    cur = conn.cursor()

    if source == 'db':
        # Database se gaana uthao
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        
        # Next song logic
        cur.execute("SELECT id FROM songs WHERE id > %s LIMIT 1", (song_id,))
        next_res = cur.fetchone()
        next_id = next_res[0] if next_res else None
        
        cur.close()
        conn.close()
        return render_template('player.html', song=song, next_id=next_id, source='db')
    
    else:
        # YouTube mode: Dummy list banakar bhej rahe hain taaki template na phate
        # Format: [id, title, youtube_id, category, audio_url]
        song = [song_id, title_fb, song_id, 'YouTube Global', '']
        cur.close()
        conn.close()
        return render_template('player.html', song=song, next_id=None, source='yt')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/recents')
def recents():
    return render_template('recents.html')

@app.route('/admin')
def admin():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM songs ORDER BY id DESC')
    songs = cur.fetchall()
    cur.execute('SELECT * FROM search_logs ORDER BY last_searched DESC')
    logs = cur.fetchall()
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
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
