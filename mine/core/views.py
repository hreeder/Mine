import requests
import urlparse

from flask import render_template, url_for, request, redirect
from flask.ext.login import login_user, logout_user, current_user

from mine import db
from mine.core import core
from mine.core.forms import WebSignInForm
from mine.core.models import User


@core.route("/")
def index():
    return render_template("core/index.html")


@core.route("/login", methods=['GET', 'POST'])
def login():
    form = WebSignInForm()
    form.client_id.data = url_for('core.index', _external=True)
    form.redirect_uri.data = url_for('core.login_callback', _external=True)

    return render_template("core/login.html", form=form)


@core.route("/login/callback", methods=['GET', 'POST'])
def login_callback():
    me = request.args["me"]
    code = request.args["code"]

    payload = {
        'client_id': url_for('core.index', _external=True),
        'redirect_uri': url_for('core.login_callback', _external=True),
        'code': code
    }

    r = requests.post('https://indieauth.com/auth', data=payload)

    if r.status_code == 200:
        response = urlparse.parse_qs(r.text)
        if response['me'][0] == me:
            # We're grand, let's get or make a user object
            user = User.query.filter_by(domain=me).first()
            if not user:
                user = User(domain=me)
                db.session.add(user)
                db.session.commit()
            login_user(user)

            return redirect(url_for('core.index'))
    else:
        # r.status_code should be 404 at this point
        # though all we care about is that it didn't 200
        return redirect(url_for('core.login'))


@core.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('core.index'))


@core.route("/micropub")
def micropub_endpoint():
    return "!"
