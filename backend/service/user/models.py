from service.shared.models import db

class User(db.Model):
    id = db.Column(db.String(22), primary_key=True)
    google_auth = db.Column(db.String(1024))