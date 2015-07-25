from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.migrate import Migrate
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

# Load Extensions
db = SQLAlchemy(app)
lm = LoginManager(app)
migrate = Migrate(app, db)

# Load Blueprintsf
from mine.admin import admin
from mine.core import core

app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(core)


# We're going to inject a variable called "site"
# which contains some global site variables
# TODO: Move these to redis, maybe pull values on demand?
@app.context_processor
def inject_site_variable():
    return dict(site={
            "title": "Harry Reeder"
        })
