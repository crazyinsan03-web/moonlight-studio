from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from youtubesearchpython import VideosSearch  # <--- Nayi Library

# ... Tera purana get_db_connection wala code ...

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Database mein dhoondo
    cur.execute("SELECT id, title, youtube_id, category FROM songs WHERE title ILIKE %s", (f'%{query}%',))
    db_results = cur.fetchall()

    # 2. Agar DB mein nahi mila, toh YouTube se uthao
    if not db_results:
        videosSearch = VideosSearch(query, limit=5)
        yt_results = videosSearch.result()['result']
        
        # Search Log: Yaad rakhne ke liye ki ye gaana missing hai
        cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Not Found') ON CONFLICT DO NOTHING", (query,))
        conn.commit()

        fallback_songs = []
        for v in yt_results:
            fallback_songs.append({
                'id': v['id'], 
                'title': v['title'], 
                'youtube_id': v['id'], 
                'category': 'YouTube Global'
            })
        
        cur.close()
        conn.close()
        return render_template('search_results.html', songs=fallback_songs, source='yt')

    cur.close()
    conn.close()
    return render_template('search_results.html', songs=db_results, source='db')

@app.route('/player/<string:song_id>')
def player(song_id):
    source = request.args.get('source', 'db')
    conn = get_db_connection()
    cur = conn.cursor()

    if source == 'db':
        # Database wala gaana (MP3 Indexing fix ke saath)
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('player.html', song=song, source='db')
    else:
        # YouTube wala gaana
        title = request.args.get('title', 'YouTube Stream')
        # Dummy list banayi hai taaki template crash na ho
        song = [song_id, title, song_id, 'YouTube Global', ''] 
        cur.close()
        conn.close()
        return render_template('player.html', song=song, source='yt')
