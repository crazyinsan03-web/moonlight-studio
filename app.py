import psycopg2
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
# Tera Neon DB URL ekdum sahi hai
DB_URL = "postgresql://neondb_owner:npg_M7CR8fwVjeNY@ep-blue-union-an1h5dmf-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- HTML ROUTES ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        title = request.form.get('title')
        yt_id = request.form.get('link')  # Manual YouTube ID
        audio_url = request.form.get('audio_url')  # Manual Archive Link
        category = request.form.get('category')
        
        cur.execute('''
            INSERT INTO songs (title, youtube_id, yt_id, audio_url, category, is_mp3) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (title, yt_id, yt_id, audio_url, category, True))
        conn.commit()
        return "<script>alert('Bhai, Gaana Add Ho Gaya!'); window.location.href='/admin';</script>"

    cur.execute('SELECT * FROM songs ORDER BY id DESC')
    songs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', songs=songs)

        


@app.route('/')
def index():
    songs = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Database se saare gaane uthao
        cur.execute('SELECT * FROM songs ORDER BY id DESC')
        songs = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    return render_template('index.html', songs=songs)

@app.route('/recents')
def recents_page():
    return render_template('recents.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/player/<int:song_id>')
def player(song_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM songs WHERE id = %s', (song_id,))
        song = cur.fetchone()
        
        cur.execute('SELECT id FROM songs WHERE id > %s ORDER BY id ASC LIMIT 1', (song_id,))
        next_song = cur.fetchone()
        next_id = next_song[0] if next_song else None
        
        cur.close()
        conn.close()
        
        if song:
            return render_template('player.html', song=song, next_id=next_id)
        return "Bhai, gaana nahi mila!", 404
    except Exception as e:
        return f"Error: {e}"

# --- API ROUTES (NEON DATABASE) ---


@app.route('/add-history', methods=['POST'])
def add_history():
    data = request.json
    phone = data.get('phone')
    song_id = data.get('song_id')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Nayi history insert karo
        cur.execute('INSERT INTO history (user_phone, song_id) VALUES (%s, %s)', (phone, song_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})






@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user already exists
        cur.execute('SELECT phone FROM users WHERE phone = %s', (phone,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"status": "error", "message": "Number pehle se registered hai!"})

        # Naya user insert karo
        cur.execute('INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)', (name, phone, password))
        conn.commit()
        
        cur.close()
        conn.close()
        return jsonify({"status": "success", "user_name": name})
    except Exception as e:
        return jsonify({"status": "error", "message": "Signup failed: " + str(e)})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT name FROM users WHERE phone = %s AND password = %s', (phone, password))
        user = cur.fetchone()
        
        cur.close()
        conn.close()

        if user:
            return jsonify({"status": "success", "user_name": user[0]})
        else:
            return jsonify({"status": "error", "message": "Phone number ya password galat hai!"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Login failed: " + str(e)})

if __name__ == '__main__':
    app.run(debug=True)
