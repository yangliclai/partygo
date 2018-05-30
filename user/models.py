from application import db
import datetime

class User(db.Document):
    name = db.StringField(require=True)
    email = db.StringField(require=True,unique=True)
    password = db.StringField(required=True)
    created = db.DateTimeField(default=datetime.datetime.now)
    bio = db.StringField(max_length=200)
    profile_image = db.StringField()