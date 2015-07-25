from flask.ext.login import UserMixin

from mine import db, lm


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(256))

    superuser = db.Column(db.Boolean, default=False)


@lm.user_loader
def load_user(userid):
        return User.query.get(userid)
