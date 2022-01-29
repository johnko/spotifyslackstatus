"""
Prerequisites

    pip3 install spotipy Flask Flask-Session

    // from your [app settings](https://developer.spotify.com/dashboard/applications)
    export SPOTIPY_CLIENT_ID=client_id_here
    export SPOTIPY_CLIENT_SECRET=client_secret_here
    export SPOTIPY_REDIRECT_URI='http://127.0.0.1:8080' // must contain a port
    // SPOTIPY_REDIRECT_URI must be added to your [app settings](https://developer.spotify.com/dashboard/applications)
    OPTIONAL
    // in development environment for debug output
    export FLASK_ENV=development
    // so that you can invoke the app outside of the file's directory include
    export FLASK_APP=/path/to/spotipy/examples/app.py
 
    // on Windows, use `SET` instead of `export`

Run app.py

    python3 app.py OR python3 -m flask run
    NOTE: If receiving "port already in use" error, try other ports: 5000, 8090, 8888, etc...
        (will need to be updated in your Spotify app and SPOTIPY_REDIRECT_URI variable)
"""

from slack_sdk import WebClient
import os
from flask import Flask, session, request, redirect
from flask_session import Session
import spotipy
import uuid
sss_uri = os.environ["SPOTIPY_REDIRECT_URI"]

slack_client_id = os.environ["SLACK_CLIENT_ID"]
slack_client_secret = os.environ["SLACK_CLIENT_SECRET"]
slack_oauth_scope = 'users.profile%3Awrite%2Cusers.profile%3Aread'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get('uuid')


@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}"><button id="login-button" data-testid="login-button" class="Button-qlcn5g-0 frUdWl"><div class="ButtonInner-sc-14ud5tc-0 lbsIMA encore-bright-accent-set"><p class="Type__TypeElement-goli3j-0 dmuHFl sc-dkPtRN giKhHg">Connect Spotify</p></div><div class="ButtonFocus-sc-2hq6ey-0 eiuQDg"></div></button></a></h2>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    session['state'] = str(uuid.uuid4())
    slack_login_button = '<a href="https://slack.com/oauth/v2/authorize?' \
        f'user_scope={slack_oauth_scope}&redirect_uri={sss_uri}/slack/oauth_redirect&client_id={slack_client_id}&state={session["state"]}" ' \
        'style="align-items:center;color:#fff;background-color:#4A154B;border:0;border-radius:56px;display:inline-flex;' \
        'font-family:Lato, sans-serif;font-size:18px;font-weight:600;height:56px;justify-content:center;text-decoration:none;width:276px">' \
        '<svg xmlns="http://www.w3.org/2000/svg" style="height:24px;width:24px;margin-right:12px" viewBox="0 0 122.8 122.8"><path d="M25.8 77.6c0 7.1-5.8 12.9-12.9 12.9S0 84.7 0 77.6s5.8-12.9 12.9-12.9h12.9v12.9zm6.5 0c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9v32.3c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V77.6z" fill="#e01e5a"></path><path d="M45.2 25.8c-7.1 0-12.9-5.8-12.9-12.9S38.1 0 45.2 0s12.9 5.8 12.9 12.9v12.9H45.2zm0 6.5c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H12.9C5.8 58.1 0 52.3 0 45.2s5.8-12.9 12.9-12.9h32.3z" fill="#36c5f0"></path><path d="M97 45.2c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9-5.8 12.9-12.9 12.9H97V45.2zm-6.5 0c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V12.9C64.7 5.8 70.5 0 77.6 0s12.9 5.8 12.9 12.9v32.3z" fill="#2eb67d"></path><path d="M77.6 97c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9-12.9-5.8-12.9-12.9V97h12.9zm0-6.5c-7.1 0-12.9-5.8-12.9-12.9s5.8-12.9 12.9-12.9h32.3c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H77.6z" fill="#ecb22e"></path></svg>' \
        'Add to Slack</a>'
    slack_status_menu = f'<a href="/get_slack_status_text">get_slack_status_text</a> | ' \
        f'<a href="/set_slack_status_text">set_slack_status_text</a>'
    show_slack_button = ''
    if session.get('SLACK_USER_TOKEN') is None:
        show_slack_button = slack_login_button
    else:
        client = WebClient(token=session['SLACK_USER_TOKEN'])
        response = client.users_profile_get()
        if not response["ok"]:
            show_slack_button = slack_login_button
        else:
            show_slack_button = slack_status_menu

    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/currently_playing">currently playing</a> | ' \
        f'<a href="/current_user">current_user</a>' \
        f'<br/><br/>' \
        f'{show_slack_button}' \



@app.route('/sign_out')
def sign_out():
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


def get_current_track():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    return track


@app.route('/currently_playing')
def currently_playing():
    track = get_current_track()
    if not track is None:
        if track['is_playing']:
            return f'{track}<br/><br/><a href="/">Return</a>'
    return 'No track currently playing.<br/><br/><a href="/">Return</a>'


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user = spotify.current_user()
    return f'{user}<br/><br/><a href="/">Return</a>'


@app.route("/slack/oauth_redirect", methods=["GET"])
def post_install():
    """
    Slack redirect to get the User Scoped Token
    """
    # Verify the "state" parameter
    assert session['state'] == request.args['state']

    # Retrieve the auth code from the request params
    code_param = request.args['code']

    # An empty string is a valid token for this request
    client = WebClient()

    # Request the auth tokens from Slack
    response = client.oauth_v2_access(
        client_id=slack_client_id,
        client_secret=slack_client_secret,
        code=code_param
    )

    # Save the bot token to an environmental variable or to your data store
    # for later use
    session["SLACK_USER_TOKEN"] = response.get(
        'authed_user').get('access_token')

    # Don't forget to let the user know that OAuth has succeeded!
    return 'App installed to Slack!<br/><br/><a href="/">Return</a>'


@app.route('/get_slack_status_text')
def get_slack_status_text():
    client = WebClient(token=session['SLACK_USER_TOKEN'])
    response = client.users_profile_get()
    assert response["ok"]
    slack_status_text = response.get('profile').get('status_text')
    if (not slack_status_text is None) and (len(slack_status_text) > 0):
        return f'Read Slack Status: {slack_status_text}<br/><br/><a href="/">Return</a>'
    return 'No Slack status currently set.<br/><br/><a href="/">Return</a>'


@app.route('/set_slack_status_text')
def set_slack_status_text():
    client = WebClient(token=session['SLACK_USER_TOKEN'])
    track = get_current_track()
    artist_title = f"{track['item']['artists'][0]['name']} - {track['item']['name']}"
    if (not artist_title is None) and (len(artist_title) > 0) and (track['is_playing']):
        response = client.users_profile_set(
            profile={
                'status_text': artist_title,
                'status_emoji': ':musical_note:',
            }
        )
        assert response["ok"]
        slack_status_text = response.get('profile').get('status_text')
        if (not slack_status_text is None) and (len(slack_status_text) > 0):
            return f'Wrote Slack Status: {slack_status_text}<br/><br/><a href="/">Return</a>'
    else:
        response = client.users_profile_set(
            profile={
                'status_text': '',
                'status_emoji': '',
            }
        )
        assert response["ok"]
    return 'No track currently playing. No Slack status currently set.<br/><br/><a href="/">Return</a>'


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))