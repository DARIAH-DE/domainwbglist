#!/usr/bin/python

import sys, os
import logging

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

activate_this = os.path.join(os.path.dirname(__file__), 'venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from listsort import app as application

