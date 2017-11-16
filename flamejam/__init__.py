import os
from flask import Flask
from datetime import datetime
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from flask_principal import Principal, Permission, RoleNeed
from flask_login import LoginManager, current_user

app = Flask(__name__)

app.config.from_pyfile('../doc/flamejam.cfg.default')
if os.environ.get('CONFIG_TYPE') == "production":
    app.config.from_pyfile('/etc/flamejam/flamejam.cfg', silent=True)
else:
    app.config.from_pyfile('../flamejam.cfg', silent=True)

mail = Mail(app)
db = SQLAlchemy(app)
markdown_object = Markdown(app, safe_mode="escape")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

principals = Principal(app)
admin_permission = Permission(RoleNeed('admin'))

from flamejam.utils import get_current_jam
import flamejam.filters
import flamejam.views.account
import flamejam.views.admin
import flamejam.views.ajax
import flamejam.views.game
import flamejam.views.index
import flamejam.views.jams
import flamejam.views.misc
import flamejam.views.team
import flamejam.models.comment
import flamejam.models.game
import flamejam.models.gamepackage
import flamejam.models.gamescreenshot
import flamejam.models.invitation
import flamejam.models.jam
import flamejam.models.participation
import flamejam.models.rating
import flamejam.models.team
import flamejam.models.user
from flamejam.cli import register_cli
register_cli(app)


@app.context_processor
def inject():
    return dict(current_user=current_user,
                current_datetime=datetime.utcnow(),
                current_jam=get_current_jam(),
                RATING_CATEGORIES=flamejam.models.rating.RATING_CATEGORIES)
