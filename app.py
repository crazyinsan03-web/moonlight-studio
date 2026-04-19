from youtubesearchpython import VideosSearch

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Pehle Database mein check karo
    cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE title ILIKE %s", (f'%{query}%',))
    db_results = cur.fetchall()

    if db_results:
        # Log Found: Agar mil gaya
        cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Found') ON CONFLICT DO NOTHING", (query,))
        conn.commit()
        return render_template('search_results.html', songs=db_results, source='db')

    else:
        # 2. Agar nahi mila toh YouTube par dhoondo
        videosSearch = VideosSearch(query, limit = 5)
        yt_results = videosSearch.result()['result']
        
        fallback_songs = []
        for video in yt_results:
            fallback_songs.append({
                'id': video['id'], # YouTube string ID
                'title': video['title'],
                'youtube_id': video['id'],
                'category': 'YouTube Global'
            })
        
        # Log Not Found: Taaki tu baad mein add kar sake
        cur.execute("INSERT INTO search_logs (query_text, status) VALUES (%s, 'Not Found')", (query,))
        conn.commit()
        
        cur.close()
        conn.close()
        return render_template('search_results.html', songs=fallback_songs, source='yt')

@app.route('/player/<string:song_id>')
def player(song_id):
    source = request.args.get('source', 'db')
    conn = get_db_connection()
    cur = conn.cursor()

    if source == 'db':
        # Database se MP3 wala logic
        cur.execute("SELECT id, title, youtube_id, category, audio_url FROM songs WHERE id = %s", (song_id,))
        song = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('player.html', song=song, source='db')
    else:
        # YouTube Global wala logic (Yahan DB ki zaroorat nahi)
        # Hum dummy song object banayenge search results se data leke
        title = request.args.get('title', 'Unknown Title')
        song = [song_id, title, song_id, 'YouTube Global', ''] 
        return render_template('player.html', song=song, source='yt')
