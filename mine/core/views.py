import requests
import urlparse

from flask import render_template, url_for, request, redirect, abort, make_response
from flask.ext.login import login_user, logout_user, current_user
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, FOAF, DCTERMS
from sqlalchemy import extract, desc

from mine import db
from mine.core import core, AS
from mine.core.forms import WebSignInForm
from mine.core.models import User, Entry, EntryMeta


@core.route("/")
@core.route("/page/<int:pagenumber>")
def index(pagenumber=1):
    page = Entry.query.order_by(desc(Entry.created_at)).paginate(pagenumber,per_page=10)
    return render_template("core/index.html", page=page, pagenumber=pagenumber)


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


@core.route("/foaf")
def foaf():
    accepts = request.headers['Accept']
    g = Graph()
    g.namespace_manager.bind("foaf", FOAF)
    me = URIRef(url_for('core.foaf', _external=True) + "#me")
    g.add((me, RDF.type, FOAF.Person))
    g.add((me, FOAF.name, Literal("Harry Reeder")))
    g.add((me, FOAF.homepage, URIRef("http://harryreeder.co.uk")))
    g.add((me, FOAF.img, URIRef("http://www.gravatar.com/avatar/882fea3f994a649328155e5ab2316b7f?s=200")))
    g.add((me, FOAF.mbox, URIRef("mailto:harry@harryreeder.co.uk")))
    if "text/turtle" in accepts:
        r = make_response(g.serialize(format='turtle'))
        r.content_type = "text/turtle"
        return r
#         return """@prefix foaf: <http://xmlns.com/foaf/0.1/> .
#
# <http://harryreeder.co.uk/foaf>
#     a foaf:Person ;
#     foaf:name "Harry Reeder" ;
#     foaf:homepage <http://harryreeder.co.uk/> ;
#     foaf:img <http://www.gravatar.com/avatar/882fea3f994a649328155e5ab2316b7f?s=200> ;
#     foaf:mbox <mailto:harry@harryreeder.co.uk> ."""
    return redirect(url_for('core.index'))


@core.route("/webmention", methods=['POST'])
def webmention_endpoint():
    source = request.form['source']
    target = request.form['target']

    return "", 200


@core.route("/micropub", methods=['GET', 'POST'])
def micropub_endpoint():
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

        slug = None
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

        if "in-reply-to" in request.form:
            reply = EntryMeta(
                entry_id=entry.id,
                predicate="in-reply-to",
                object=request.form['in-reply-to']
            )
            db.session.add(reply)

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
        entry.syndicate()
        response.headers['Location'] = loc
        return response

    return abort(404)


@core.route("/<int:year>/<int:month>/<id>")
@core.route("/<int:year>/<int:month>/<id>-<slug>")
def get_entry(year, month, id, slug=None):
    entry = Entry.query.filter(extract('year', Entry.created_at) == year).filter(extract('month', Entry.created_at) == month).filter_by(id=id).first_or_404()

    g = Graph()
    g.namespace_manager.bind("as", AS)
    g.namespace_manager.bind("dcterms", DCTERMS)
    if slug:
        me = URIRef(url_for('core.get_entry', year=year, month=month, id=id, slug=slug, _external=True))
    else:
        me = URIRef(url_for('core.get_entry', year=year, month=month, id=id, _external=True))

    if entry.name:
        g.add((me, RDF.type, AS.Article))
        g.add((me, AS.displayName, Literal(entry.name)))
    else:
        g.add((me, RDF.type, AS.Note))

    g.add((me, AS.content, Literal(entry.content)))
    g.add((me, AS.published, Literal(entry.created_at)))
    g.add((me, DCTERMS.identifier, Literal(entry.id)))

    if entry.in_reply_to:
        g.add((me, AS.inReplyTo, URIRef(entry.in_reply_to)))

    accepts = request.headers['Accept']
    if "text/turtle" in accepts:
        r = make_response(g.serialize(format='turtle'))
        r.content_type = "text/turtle"
        return r

    return render_template("core/entry.html", entry=entry)
