from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.markdown import Markdown
from flask.ext.migrate import Migrate
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import exc, event
from sqlalchemy.pool import Pool


app = Flask(__name__)
app.config.from_object('config')

# Load Extensions
db = SQLAlchemy(app)
lm = LoginManager(app)
md = Markdown(app, extensions=['markdown.extensions.fenced_code'])
migrate = Migrate(app, db)

# Load Blueprints
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

# Fix for "MySQL server has gone away"
@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_con, con_record, con_proxy):
    cur = dbapi_con.cursor()
    try:
        cur.execute("SELECT 1")
    except:
        raise exc.DisconnectionError()
    cur.close()
