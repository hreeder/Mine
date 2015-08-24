from flask import Blueprint
from rdflib.namespace import Namespace

core = Blueprint('core', __name__, template_folder="templates")

AS = Namespace("http://www.w3.org/ns/activitystreams#")

from mine.core import views
