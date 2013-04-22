from distutils.core import setup
import fnmatch
import os

setup(
    name='flamejam',
    description='A generic game jam application with ratings and comments using Flask',
    version='0.2',
    url = "https://github.com/svenstaro/flamejam/",
    long_description=__doc__,
    packages=['flamejam'],
    package_data={'flamejam': ['templates/*.html', 'templates/account/*.html', 'templates/admin/*.html',
                               'templates/emails/*.html', 'templates/jam/*.html', 'templates/misc/*.html']},
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'flask-mail', 'flask-sqlalchemy', 'flask-wtf',
                      'flask-login', 'flask-markdown', 'python-dateutil',
                      'scrypt', 'requests', 'alembic', 'flask-principal', 'fabric'],
    scripts=['runserver.py', 'kill-database.py'],
    data_files=[('/etc/flamejam/alembic', ['alembic.ini', 'alembic/env.py', 'alembic/README', 'alembic/script.py.mako']),
                ('/usr/share/flamejam', ['flamejam.cfg.default', 'flamejam.wsgi.example', 'README.md', 'LICENSE'])]
)
