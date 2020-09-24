from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix

# csrf protection object
csrf = CSRFProtect()

app = Flask(__name__, static_url_path="/static")
app.config.from_object(Config)
# implement csrf protection
csrf.init_app(app)

app.wsgi_app = ProxyFix(app.wsgi_app)

db = SQLAlchemy(app)

from . import routes
