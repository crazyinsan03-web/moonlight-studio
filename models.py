from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    # YouTube ki 11-digit ID save karne ke liye
    video_id = db.Column(db.String(100), nullable=False)
    # Thumbnail ki link lambi ho sakti hai isliye Text use kiya hai
    thumbnail = db.Column(db.Text)
    # Optional: Agar kabhi date wise sort karna ho
    # created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Song {self.title}>'
