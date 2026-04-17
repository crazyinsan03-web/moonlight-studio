from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    # Ye dono 'Text' hone chahiye, 'String(200)' nahi!
    song_url = db.Column(db.Text) 
    thumbnail = db.Column(db.Text)
