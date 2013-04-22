from flask import Flask
from datetime import *
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown
from flask.ext.principal import Principal, Permission, RoleNeed
from flask.ext.login import LoginManager, current_user
from flask_errormail import mail_on_500

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

mail_on_500(app, app.config['ADMINS'])

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))

from flamejam.utils import *
import flamejam.filters
import flamejam.views
import flamejam.models

@app.context_processor
def inject():
    return dict(current_user = current_user,
        current_datetime = datetime.utcnow(),
        current_jam = get_current_jam(),
        RATING_CATEGORIES = flamejam.models.rating.RATING_CATEGORIES)
