import os
from os import environ
from flask import Flask
from config import Config

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)
app.secret_key = os.urandom(24)

from app import routes
