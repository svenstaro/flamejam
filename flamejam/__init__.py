from flask import Flask
from datetime import *
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.markdown import Markdown

app = Flask(__name__)
mail = Mail(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flamejam.db'
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'lolsecret'
#app.config['REDDIT_SERVER'] = 'reddit.com'
#app.config['REDDIT_CONFIRM_THREAD'] = 'http://reddit.com/r/test/comments/iot3h/api_test/'
app.config.from_pyfile('../flamejam.cfg', silent=True)
app.config.from_pyfile('../recaptcha.cfg', silent=True)
db = SQLAlchemy(app)
markdown_object = Markdown(app, safe_mode="escape")

from flamejam.utils import *
import flamejam.filters
import flamejam.views
import flamejam.models
import flamejam.login

@app.context_processor
def inject():
    a = flamejam.models.Announcement.query.order_by(flamejam.models.Announcement.posted.desc()).first()
    return dict(last_announcement = a,
        current_user = flamejam.login.get_current_user(),
        current_datetime = datetime.utcnow(),
        current_jam = get_current_jam(),
        RATING_CATEGORIES = flamejam.models.rating.RATING_CATEGORIES)

