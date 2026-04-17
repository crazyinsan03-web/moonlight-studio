from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    song_url = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.Text, nullable=True)
