"""
Modified from

    https://github.com/plamere/spotipy/blob/master/examples/app.py
    MIT Licensed https://github.com/plamere/spotipy/blob/master/LICENSE.md

    https://github.com/slackapi/python-slack-sdk/blob/main/docs/installation/index.html
    MIT Licensed https://github.com/slackapi/python-slack-sdk/blob/main/LICENSE

Prerequisites

    pip3 install spotipy Flask Flask-Session

    // from your [app settings](https://developer.spotify.com/dashboard/applications)
    export SPOTIFY_CLIENT_ID=client_id_here
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
from flask import Flask, request, redirect
import flask.sessions
from flask_dynamodb_sessions import Session
import spotipy
import uuid
import boto3
sss_uri = os.environ["SPOTIPY_REDIRECT_URI"]

ssm_session = boto3.session.Session()
ssm_client = client = ssm_session.client(
    service_name='ssm',
    region_name=os.environ["AWS_REGION"],
)

os.environ['SPOTIPY_CLIENT_ID']     = ssm_client.get_parameter(Name='SPOTIFY_CLIENT_ID', WithDecryption=False).get('Parameter').get('Value')
os.environ['SPOTIPY_CLIENT_SECRET'] = ssm_client.get_parameter(Name='SPOTIFY_CLIENT_SECRET', WithDecryption=True).get('Parameter').get('Value')
os.environ['SLACK_CLIENT_ID']     = ssm_client.get_parameter(Name='SLACK_CLIENT_ID', WithDecryption=False).get('Parameter').get('Value')
os.environ['SLACK_CLIENT_SECRET'] = ssm_client.get_parameter(Name='SLACK_CLIENT_SECRET', WithDecryption=True).get('Parameter').get('Value')

slack_client_id = os.environ["SLACK_CLIENT_ID"]
slack_client_secret = os.environ["SLACK_CLIENT_SECRET"]
slack_oauth_scope = 'users.profile%3Awrite%2Cusers.profile%3Aread'

app = Flask(__name__)
# app.config['SECRET_KEY'] = os.urandom(64)
app.config.update(
    SESSION_DYNAMODB_TABLE=os.environ['SESSION_DYNAMODB_TABLE'],
    SESSION_DYNAMODB_REGION=os.environ.get('SESSION_DYNAMODB_REGION',
        os.environ.get('AWS_REGION', 'ca-central-1')
    ),
    SESSION_DYNAMODB_TTL_SECONDS=os.environ.get('SESSION_DYNAMODB_TTL_SECONDS', 86400 * 7)
)
Session(app)


@app.route('/')
def index():
    if not flask.session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        flask.session['uuid'] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.DjangoSessionCacheHandler(flask)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(
            code=request.args.get("code"),
            as_dict=False,
        )
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2>SpotifySlackStatus</h2><a href="{auth_url}">' \
            '<button id="login-button" data-testid="login-button" class="Button-qlcn5g-0 frUdWl" ' \
            'style="cursor: pointer;box-sizing: border-box;font-family: spotify-circular, Helvetica, Arial, sans-serif;-webkit-tap-highlight-color: transparent;font-weight: 700;background-color: transparent;border: 0px;border-radius: 500px;display: inline-block;position: relative;text-align: center;text-decoration: none;touch-action: manipulation;transition-duration: 33ms;transition-property: background-color, border-color, color, box-shadow, filter, transform;user-select: none;vertical-align: middle;transform: translate3d(0px, 0px, 0px);padding: 0px;align-self: center;">' \
            '<div class="ButtonInner-sc-14ud5tc-0 lbsIMA encore-bright-accent-set" ' \
            'style="position: relative;background-color: var(--background-base,#1ed760);color: var(--text-base,#000000);border-radius: 500px;font-size: inherit;padding: 14px 32px;">' \
            '<p class="Type__TypeElement-goli3j-0 dmuHFl sc-dkPtRN giKhHg" style="text-transform: uppercase;box-sizing: border-box;font-family: spotify-circular, Helvetica, Arial, sans-serif;-webkit-tap-highlight-color: transparent;margin-top: 0px;margin-bottom: 0px;color: inherit;font-weight: 700;">' \
            'Connect Spotify</p></div></button></a>'

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    flask.session['state'] = str(uuid.uuid4())

    slack_login_button = '<a href="https://slack.com/oauth/v2/authorize?' \
        f'user_scope={slack_oauth_scope}&redirect_uri={sss_uri}/slack/oauth_redirect&client_id={slack_client_id}&state={flask.session["state"]}" ' \
        'style="align-items:center;color:#fff;background-color:#4A154B;border:0;border-radius:56px;display:inline-flex;' \
        'font-family:Lato, sans-serif;font-size:18px;font-weight:600;height:56px;justify-content:center;text-decoration:none;width:276px">' \
        '<svg xmlns="http://www.w3.org/2000/svg" style="height:24px;width:24px;margin-right:12px" viewBox="0 0 122.8 122.8"><path d="M25.8 77.6c0 7.1-5.8 12.9-12.9 12.9S0 84.7 0 77.6s5.8-12.9 12.9-12.9h12.9v12.9zm6.5 0c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9v32.3c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V77.6z" fill="#e01e5a"></path><path d="M45.2 25.8c-7.1 0-12.9-5.8-12.9-12.9S38.1 0 45.2 0s12.9 5.8 12.9 12.9v12.9H45.2zm0 6.5c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H12.9C5.8 58.1 0 52.3 0 45.2s5.8-12.9 12.9-12.9h32.3z" fill="#36c5f0"></path><path d="M97 45.2c0-7.1 5.8-12.9 12.9-12.9s12.9 5.8 12.9 12.9-5.8 12.9-12.9 12.9H97V45.2zm-6.5 0c0 7.1-5.8 12.9-12.9 12.9s-12.9-5.8-12.9-12.9V12.9C64.7 5.8 70.5 0 77.6 0s12.9 5.8 12.9 12.9v32.3z" fill="#2eb67d"></path><path d="M77.6 97c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9-12.9-5.8-12.9-12.9V97h12.9zm0-6.5c-7.1 0-12.9-5.8-12.9-12.9s5.8-12.9 12.9-12.9h32.3c7.1 0 12.9 5.8 12.9 12.9s-5.8 12.9-12.9 12.9H77.6z" fill="#ecb22e"></path></svg>' \
        'Add to Slack</a>'
    slack_status_menu = f'<a href="/get_slack_status_text">get_slack_status_text</a>' \
        f'<br/><br/>' \
        f'<a href="/set_slack_status_text">set_slack_status_text</a>'
    show_slack_button = ''
    if flask.session.get('SLACK_USER_TOKEN') is None:
        show_slack_button = slack_login_button
    else:
        client = WebClient(token=flask.session['SLACK_USER_TOKEN'])
        response = client.users_profile_get()
        if not response["ok"]:
            show_slack_button = slack_login_button
        else:
            show_slack_button = slack_status_menu

    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
        f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
        f'<a href="/currently_playing">currently playing</a>' \
        f'<br/><br/>' \
        f'<a href="/current_user">current_user</a>' \
        f'<br/><br/>' \
        f'{show_slack_button}' \



@app.route('/sign_out')
def sign_out():
    try:
        flask.session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


def get_current_track():
    cache_handler = spotipy.cache_handler.DjangoSessionCacheHandler(flask)
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
        return f'{track}' \
            '<br/><br/><a href="/">Return</a>'
    return 'No track currently playing.' \
        '<br/><br/><a href="/">Return</a>'


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.DjangoSessionCacheHandler(flask)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    user = spotify.current_user()
    return f'{user}' \
        '<br/><br/><a href="/">Return</a>'


@app.route("/slack/oauth_redirect", methods=["GET"])
def post_install():
    """
    Slack redirect to get the User Scoped Token
    """
    # Verify the "state" parameter
    assert flask.session['state'] == request.args['state']

    # Retrieve the auth code from the request params
    code_param = request.args.get('code')

    if not code_param is None:
        # An empty string is a valid token for this request
        client = WebClient()

        try:
            # Request the auth tokens from Slack
            response = client.oauth_v2_access(
                client_id=slack_client_id,
                client_secret=slack_client_secret,
                code=code_param
            )
        except:
            return 'Error installing SpotifySlackStatus app to Slack...' \
                '<br/><br/><a href="/">Return</a>'
        # Save the bot token to an environmental variable or to your data store
        # for later use
        flask.session["SLACK_USER_TOKEN"] = response.get(
            'authed_user').get('access_token')

        if not flask.session["SLACK_USER_TOKEN"] is None:
            # Don't forget to let the user know that OAuth has succeeded!
            return 'SpotifySlackStatus app successfully installed to Slack!' \
                '<br/><br/><a href="/">Return</a>'
    return 'Error installing SpotifySlackStatus app to Slack...' \
        '<br/><br/><a href="/">Return</a>'


def get_saved_status():
    original_status_emoji = flask.session.get('slack_status_emoji')
    original_status_text = flask.session.get('slack_status_text')
    saved_status = ''
    if (not original_status_emoji is None) or (not original_status_text is None):
        if original_status_emoji is None:
            original_status_emoji = ''
        if original_status_text is None:
            original_status_text = ''
        saved_status = f'Original Slack Status (before SpotifySlackStatus):' \
            '<br/><br/>' \
            f"{original_status_emoji}" \
            f'<br/>' \
            f"{original_status_text}" \
            '<br/><br/>'
    return saved_status


@app.route('/get_slack_status_text')
def get_slack_status_text():
    client = WebClient(token=flask.session['SLACK_USER_TOKEN'])
    response = client.users_profile_get()
    assert response["ok"]
    slack_status_emoji = response.get('profile').get('status_emoji')
    slack_status_text = response.get('profile').get('status_text')
    saved_status = get_saved_status()

    if ((not slack_status_emoji is None) and (len(slack_status_emoji) > 0)) or ((not slack_status_text is None) and (len(slack_status_text) > 0)):
        return f'Retrieved Slack Status:' \
            f'<br/><br/>' \
            f"{slack_status_emoji}" \
            f'<br/>' \
            f"{slack_status_text}" \
            '<br/><br/>' \
            f"{saved_status}" \
            '<a href="/">Return</a>'
    return 'No Slack status currently set.' \
        '<br/><br/><a href="/">Return</a>'


@app.route('/set_slack_status_text')
def set_slack_status_text():
    client = WebClient(token=flask.session['SLACK_USER_TOKEN'])

    # save original Slack status
    response = client.users_profile_get()
    assert response["ok"]
    current_emoji = response.get('profile').get('status_emoji')
    current_text = response.get('profile').get('status_text')
    if (not current_emoji == ':musical_note:') and (not current_emoji == ':double_vertical_bar:'):
        flask.session['slack_status_emoji'] = current_emoji
        flask.session['slack_status_text'] = current_text
    saved_status = get_saved_status()

    # find spotify track
    track = get_current_track()
    if not track is None:
        artist_title = f"{track['item']['artists'][0]['name']} - {track['item']['name']}"
        if (not artist_title is None) and (len(artist_title) > 0):
            # set emoji as paused or playing
            slack_emoji = ':double_vertical_bar:'
            if track['is_playing']:
                slack_emoji = ':musical_note:'
            response = client.users_profile_set(
                profile={
                    'status_emoji': slack_emoji,
                    'status_text': artist_title,
                }
            )
            assert response["ok"]
            slack_status_emoji = response.get('profile').get('status_emoji')
            slack_status_text = response.get('profile').get('status_text')
            if (not slack_status_text is None) and (len(slack_status_text) > 0):
                return f'Wrote Slack Status:' \
                    f'<br/><br/>' \
                    f'{slack_status_emoji}' \
                    f'<br/>' \
                    f'{slack_status_text}' \
                    f'<br/><br/>' \
                    f"{saved_status}" \
                    '<a href="/">Return</a>'
            return f'Error writing Slack Status.' \
                '<br/><br/><a href="/">Return</a>'
        return f'Error fetching current track. Not writing Slack Status.' \
            '<br/><br/><a href="/">Return</a>'
    else:
        # reset back to original
        original_status_emoji = flask.session.get('slack_status_emoji')
        original_status_text = flask.session.get('slack_status_text')
        if original_status_emoji is None:
            original_status_emoji = ''
        if original_status_text is None:
            original_status_text = ''
        response = client.users_profile_set(
            profile={
                'status_emoji': original_status_emoji,
                'status_text': original_status_text,
            }
        )
        assert response["ok"]
        return 'No track currently playing. Restoring Slack status.' \
            f'<br/><br/>' \
            f"{saved_status}" \
            '<a href="/">Return</a>'


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))
