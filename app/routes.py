from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
from flask import render_template, send_from_directory
import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from app import app

@app.route('/js/<path:path>')
def send_js(path):
    """
    Serve javascript files
    """
    return send_from_directory('js', path)

@app.route('/css/<path:path>')
def send_css(path):
    """
    Serve css files
    """
    return send_from_directory('css', path)

@app.route("/terms-of-service")
def docs_tos():
    """
    Terms of service page
    """
    return render_template('terms-of-service.html')

@app.route("/service-level-agreement")
def docs_sla():
    """
    Service level agreement page
    """
    return render_template('service-level-agreement.html')

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
    identity = OAuth2Session(app.config['CLIENT_ID'], scope=app.config['SCOPES'], redirect_uri=app.config['REDIRECT_URI'])
    authorization_url, state = identity.authorization_url(app.config['AUTHORISATION_BASE_URL'],
                                                          access_type="offline",
                                                          prompt="select_account")

    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    identity = OAuth2Session(app.config['CLIENT_ID'], redirect_uri=app.config['REDIRECT_URI'],
                             state=session.get('oauth_state'))
    token = identity.fetch_token(app.config['TOKEN_URL'], client_secret=app.config['CLIENT_SECRET'],
                                 authorization_response=request.url)

    identity = OAuth2Session(app.config['CLIENT_ID'], token=token)
    userinfo = identity.get(app.config['OIDC_BASE_URL'] + 'userinfo').json()

    allowed = False
    if app.config['REQUIRED_ENTITLEMENTS'] != '':
        if 'edu_person_entitlements' in userinfo:
            for entitlements in app.config['REQUIRED_ENTITLEMENTS']:
                num_required = len(entitlements)
                num_have = 0
                for entitlement in entitlements:
                    if entitlement in userinfo['edu_person_entitlements']:
                        num_have += 1
                if num_required == num_have:
                    allowed = True
                    break
        else:
            allowed = True
    else:
        allowed = True

    if not allowed:
        return render_template('error.html', message="You do not have the required entitlements.")
            
    data = {}
    data['username'] = userinfo['sub']
    data['refresh_token'] = token['refresh_token']
        
    try:
        response = requests.post(app.config['IMC_URL'],
                                 timeout=5,
                                 json=data,
                                 auth=HTTPBasicAuth(app.config['IMC_USERNAME'], 
                                                    app.config['IMC_PASSWORD']),
                                 cert=(app.config['IMC_SSL_CERT'],
                                       app.config['IMC_SSL_KEY']),
                                 verify=app.config['IMC_SSL_CERT'])
    except (requests.exceptions.Timeout, requests.exceptions.RequestException):
        return render_template('error.html', message="Unexpected error, please try again.")
        
    if response.status_code == 201:
        return render_template('home.html')
        
    return render_template('error.html', message="Unexpected error, please try again.")

