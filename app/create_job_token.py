import configparser
import time
import jwt

CONFIG = configparser.ConfigParser()
CONFIG.read('/etc/prominence/prominence.ini')

def create_job_token(username, groups, lifetime, ui='', email=''):
    """
    Create a jwt job token
    """
    return jwt.encode({"username": username, "groups": groups, "job": ui, "exp": int(time.time() + lifetime), "email": email},
                      CONFIG.get('credentials', 'job_token_secret'),
                      algorithm="HS256")
