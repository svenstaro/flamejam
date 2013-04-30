import sys, os
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_dir)
activate_this = os.path.join(current_dir, 'env/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))
from flamejam import app as application
