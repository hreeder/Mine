from flask import Blueprint

admin = Blueprint('admin', __name__, template_folder='templates')

from mine.admin import views
