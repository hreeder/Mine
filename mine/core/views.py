import requests
import urlparse

from flask import render_template, url_for, request, redirect, abort, make_response
from flask.ext.login import login_user, logout_user, current_user
from sqlalchemy import extract, desc

from mine import db
from mine.core import core
from mine.core.forms import WebSignInForm
from mine.core.models import User, Entry


@core.route("/")
def index():
    entries = Entry.query.order_by(desc(Entry.created_at)).limit(10).all()
    return render_template("core/index.html", entries=entries)


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


@core.route("/webmention", methods=['POST'])
def webmention_endpoint():
    source = request.form['source']
    target = request.form['target']

    return "", 200


@core.route("/micropub", methods=['GET', 'POST'])
def micropub_endpoint():
    for k in request.form:
        print k, request.form[k]

    auth = request.headers['Authorization']
    token = auth.replace("Bearer", "").strip()
    if not token:
        return abort(401)

    r = requests.get('https://tokens.indieauth.com/token', headers={'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': auth})
    if r.status_code == 200:
        data = urlparse.parse_qs(r.text)

        if data['me'][0] != url_for('core.index', _external=True) or 'post' not in data['scope']:
            return abort(403)

        entry = Entry()

        if "slug" in request.form:
            slug = request.form['slug']
        elif "name" in request.form:
            slug = request.form['name'].replace(" ", "-").lower()

        if slug:
            entry.slug = slug

        if "content" in request.form:
            content = request.form['content']
            entry.content = content

        # Store the data
        if "name" in request.form:
            entry.name = request.form['name']

        db.session.add(entry)
        db.session.commit()

        response = make_response()
        response.status_code = 201
        if slug:
            loc = url_for('core.get_entry', year=entry.created_at.year, month=entry.created_at.month, id=entry.id, slug=slug, _external=True)
            url = url_for('core.get_entry', year=entry.created_at.year, month=entry.created_at.month, id=entry.id, slug=slug)
        else:
            loc = url_for('core.get_entry', year=entry.created_at.year, month=entry.created_at.month, id=entry.id, _external=True)
            url = url_for('core.get_entry', year=entry.created_at.year, month=entry.created_at.month, id=entry.id)
        entry.url = url
        db.session.add(entry)
        db.session.commit()
        response.headers['Location'] = loc
        return response

    return abort(404)


@core.route("/<int:year>/<int:month>/<id>")
@core.route("/<int:year>/<int:month>/<id>-<slug>")
def get_entry(year, month, id, slug=None):
    entry = Entry.query.filter(extract('year', Entry.created_at) == year).filter(extract('month', Entry.created_at) == month).filter_by(id=id).first_or_404()
    print entry.content
    return render_template("core/entry.html", entry=entry)
