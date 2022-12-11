from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from flask import render_template, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from app import app
from app.create_job_token import create_job_token

@app.route('/css/<path:path>')
def send_css(path):
    """
    Serve css files
    """
    return send_from_directory('css', path)

@app.route("/")
def landing():
    """
    Login page
    """
    return render_template('index.html')

@app.route("/authorise")
def authorise():
    """
    Redirect the user/resource owner to the OAuth provider (i.e. EGI Check-in)
    using an URL with a few key OAuth parameters.
    """
    identity = OAuth2Session(app.config['CLIENT_ID'],
                             scope=app.config['SCOPES'],
                             redirect_uri=app.config['REDIRECT_URI'])
    authorization_url, state = identity.authorization_url(app.config['AUTHORISATION_BASE_URL'])

    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    identity = OAuth2Session(app.config['CLIENT_ID'],
                             redirect_uri=app.config['REDIRECT_URI'],
                             state=session.get('oauth_state'))

    # This shouldn't be needed
    authorization_response = request.url.replace('http:', 'https:')

    # Get token
    try:
        token = identity.fetch_token(app.config['TOKEN_URL'],
                                     client_secret=app.config['CLIENT_SECRET'],
                                     authorization_response=authorization_response)
    except:
        return redirect('/')

    try:
        identity = OAuth2Session(app.config['CLIENT_ID'], token=token)
        userinfo = identity.get(app.config['OIDC_USER_URL']).json()
    except:
        return render_template('error.html',
                               message="Unexpected error, please try again.")

    username = userinfo[app.config['USERNAME_MAP']]
    token = create_job_token(username,
                             app.config['DEFAULT_GROUP'],
                             app.config['DEFAULT_TOKEN_LIFETIME'],
                             email=userinfo['email'])
            
    return render_template('home.html', token=token)

@app.route('/token', methods=['POST'])
def create_token():
    """
    Create an access token from an EGI token
    """
    # Get the username
    access_token = None
    if 'token' in request.get_json():
        access_token = request.get_json()['token']

    if not access_token:
        return jsonify({}), 400

    headers = {'Authorization': 'Bearer %s' % access_token}
    try:
        response = requests.get(app.config['OIDC_USER_URL'], headers=headers)
    except:
        return jsonify({}), 400

    username = None
    if response.status_code == 200:
        if app.config['USERNAME_MAP'] in response.json():
            username = response.json()[app.config['USERNAME_MAP']]

    if not username:
        return jsonify({}), 400

    token = create_job_token(username,
                             app.config['DEFAULT_GROUP'],
                             app.config['DEFAULT_TOKEN_LIFETIME'],
                             email=response.json()['email'])

    return jsonify({'access_token': token}), 201
