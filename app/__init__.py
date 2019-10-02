import os
from flask import Flask

app = Flask(__name__, static_url_path='/static')

# Configuration
if 'PROMINENCE_WEBUI_CONFIG_FILE' in os.environ:
    app.config.from_pyfile(os.environ['PROMINENCE_WEBUI_CONFIG_FILE'])
else:
    print('ERROR: Environment variable PROMINENCE_WEBUI_CONFIG_FILE has not been defined')
    exit(1)

app.secret_key = os.urandom(24)

from app import routes
