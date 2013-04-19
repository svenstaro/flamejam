from setuptools import setup

setup(
    name='flamejam',
    version='0.2',
    long_description=__doc__,
    packages=['flamejam'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'flask-mail', 'flask-sqlalchemy', 'flask-wtf',
                      'flask-login', 'flask-markdown', 'python-dateutil',
                      'scrypt', 'requests', 'alembic', 'flask-principal', 'fabric']
)
