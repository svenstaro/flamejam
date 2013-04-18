from flask import Flask
from datetime import *
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.principal import Principal, identity_loaded, Permission, RoleNeed
from flask.ext.login import LoginManager, current_user

app = Flask(__name__)

# First load default config
app.config.from_pyfile('../flamejam.cfg.default')
# Then load user config on top of that
app.config.from_pyfile('../flamejam.cfg', silent=True)

mail = Mail(app)
db = SQLAlchemy(app)
markdown_object = Markdown(app, safe_mode="escape")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))

from flamejam.utils import *
import flamejam.filters
import flamejam.views
import flamejam.models
import flamejam.login

@app.context_processor
def inject():
    a = flamejam.models.Announcement.query.order_by(flamejam.models.Announcement.posted.desc()).first()
    return dict(last_announcement = a,
        current_user = current_user,
        current_datetime = datetime.utcnow(),
        current_jam = get_current_jam(),
        RATING_CATEGORIES = flamejam.models.rating.RATING_CATEGORIES)
