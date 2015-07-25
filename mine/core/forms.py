from flask import url_for
from flask_wtf import Form
from wtforms import HiddenField
from wtforms.fields.html5 import URLField


class WebSignInForm(Form):
    me = URLField('Your Domain', default="http://")
    client_id = HiddenField('Client ID')
    redirect_uri = HiddenField('Redirect URI')
