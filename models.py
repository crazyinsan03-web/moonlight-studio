from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    # YouTube ki 11-digit ID save karne ke liye
    video_id = db.Column(db.String(100), nullable=False)
    # Thumbnail ki link lambi ho sakti hai isliye Text use kiya hai
    thumbnail = db.Column(db.Text)
    
    # --- NAYA COLUMN ---
    # Har gaane ke likes count karne ke liye
    likes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Song {self.title}>'
