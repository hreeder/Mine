import datetime

from flask.ext.login import UserMixin

from mine import db, lm


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(256))

    superuser = db.Column(db.Boolean, default=False)


@lm.user_loader
def load_user(userid):
        return User.query.get(userid)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    slug = db.Column(db.String(64))
    url = db.Column(db.String(256))

    @property
    def like_of(self):
        return EntryMeta.query.filter_by(entry_id=self.id, predicate="like-of").first()

    @property
    def in_reply_to(self):
        return EntryMeta.query.filter_by(entry_id=self.id, predicate="in-reply-to").first()

    @property
    def repost_of(self):
        return EntryMeta.query.filter_by(entry_id=self.id, predicate="repost-of").first()


class EntryMeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    predicate = db.Column(db.String(128))
    object = db.Column(db.String(128))
