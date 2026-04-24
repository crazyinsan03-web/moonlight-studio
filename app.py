import psycopg2
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os

app = Flask(__name__)

# Tera Neon DB Connection
DB_URL = "postgresql://neondb_owner:npg_M7CR8fwVjeNY@ep-blue-union-an1h5dmf-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DB_URL)

@app.route('/')
def index():
    songs = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, title, youtube_id, category FROM songs ORDER BY RANDOM()')
        songs = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
    return render_template('index.html', songs=songs)

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query: return redirect(url_for('index'))
    conn = get_db_connection()
    cur = conn.cursor()
    # Similarity logic: 0.2 ka matlab 20% match hone par bhi result dikhayega
    cur.execute("""
        SELECT id, title, youtube_id, category 
        FROM songs 
        WHERE similarity(title, %s) > 0.2 
        ORDER BY similarity(title, %s) DESC LIMIT 15
    """, (query, query))
    songs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', songs=songs, search_query=query)

@app.route('/player/<string:song_id>')
def player(song_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        
        # Next song button ke liye logic
        cur.execute("SELECT id FROM songs WHERE id > %s LIMIT 1", (song_id,))
        next_res = cur.fetchone()
        next_id = next_res[0] if next_res else None
        
        cur.close()
        conn.close()
        return render_template('player.html', song=song, next_id=next_id, source='db')
    except:
        return redirect(url_for('index'))

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)', 
                (data.get('name'), data.get('phone'), data.get('password')))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM users WHERE phone = %s AND password = %s', 
                (data.get('phone'), data.get('password')))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return jsonify({"status": "success", "user_name": user[0]})
    return jsonify({"status": "error", "message": "Galat details!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
