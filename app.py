import os
import re
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

import os

# TERA NEON CONNECTION (Ab ye Render ke Environment se URL uthayega)
DB_URL = os.environ.get('DATABASE_URL')
def get_db_connection():
    conn = psycopg2.connect(DB_URL)
    return conn

def extract_video_id(url):
    # YouTube link se Video ID nikalne ka logic
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    video_id = re.search(pattern, url)
    if video_id:
        return video_id.group(1)
    return None

# --- MAIN PAGE ---
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    # Saare gaane load karo (Naya pehle)
    cur.execute('SELECT * FROM songs ORDER BY id DESC')
    songs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', songs=songs)

# --- PLAYER PAGE ---
@app.route('/player/<int:song_id>')
def player(song_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Database se current song fetch karo
    cur.execute('SELECT * FROM songs WHERE id = %s', (song_id,))
    song = cur.fetchone()
    
    # Next song ka logic
    cur.execute('SELECT id FROM songs WHERE id < %s ORDER BY id DESC LIMIT 1', (song_id,))
    next_song = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if song:
        return render_template('player.html', song=song, next_id=next_song[0] if next_song else None)
    return redirect(url_for('index'))

# --- LIKE SYSTEM (New Feature) ---
@app.route('/like/<int:song_id>', methods=['POST'])
def like_song(song_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Database mein likes +1 karo
        cur.execute('UPDATE songs SET likes = likes + 1 WHERE id = %s', (song_id,))
        conn.commit()
        success = True
    except:
        success = False
    cur.close()
    conn.close()
    return jsonify({"success": success})

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Agar DELETE button dabaya
        if 'delete_id' in request.form:
            song_id = request.form['delete_id']
            cur.execute('DELETE FROM songs WHERE id = %s', (song_id,))
            conn.commit()
        
        # Agar Naya Gaana add kiya
        elif 'title' in request.form:
            title = request.form['title']
            link = request.form['link']
            category = request.form.get('category', 'General')
            yt_id = extract_video_id(link)
            if yt_id:
                # yt_id, title aur category ke saath 'likes' default 0 jayega
                cur.execute('INSERT INTO songs (title, yt_id, category, likes) VALUES (%s, %s, %s, 0)',
                            (title, yt_id, category))
                conn.commit()

    # Admin page ki list refresh karo
    cur.execute('SELECT * FROM songs ORDER BY id DESC')
    songs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', songs=songs)

if __name__ == '__main__':
    # Server start karne ka command
    app.run(debug=True)
