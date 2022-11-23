import os
import json
import requests
import time
import uuid
import spotipy #pip install spotipy --upgrade
from spotipy.oauth2 import SpotifyOAuth
from helpers import create_playlist, get_songs, add_to_playlist, get_artist_uri, get_user_id, get_song_names, get_artist_name
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session



# Configure application

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(12).hex()
app.config["SESSION_COOKIE_NAME"] = "JRDN-Cookie"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

#api keys as environment variables
if not os.environ.get("client_id"):
    raise RuntimeError("client_id not set")

if not os.environ.get("secret_id"):
    raise RuntimeError("secret_id not set")

client_id = os.getenv("client_id")
secret_id = os.getenv("secret_id")

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

def session_cache_path():
    return caches_folder + session.get('uuid')

def create_spotify_oauth():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    return SpotifyOAuth(
        client_id = client_id,
        client_secret = secret_id,
        cache_path = session_cache_path(),
        redirect_uri = url_for('redirect_page', _external=True),
        scope = "playlist-modify-public",
        cache_handler = cache_handler,
        show_dialog = True
    )
#HOMEPAGE WELCOMING USERS TO THE SITE.  IF THEY PUSH THE BUTTON, THEY LOGIN WITH SPOTIFY
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        #pressing start removes token info of previous user if it exists
        session.pop("token_info", None)
        if not session.get('uuid'):
            session['uuid'] = str(uuid.uuid4())
        return render_template("login.html")
    else:
        sp_oauth = create_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

#after logging in with spotify, trade code for token and store in session
@app.route("/redirect")
def redirect_page():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id = client_id,
                                               client_secret = secret_id,
                                               scope='playlist-modify-public playlist-modify-private',
                                               redirect_uri = url_for('redirect_page', _external=True),
                                               cache_handler=cache_handler,
                                               show_dialog=True)
    if request.args.get("code"):
    # redirection
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/search')
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
    # Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    print(sp_oauth.get_cached_token())
    session["token_info"] = token_info

    return redirect("/search")


def get_token():
    try:
        token_info = session["token_info"]
    except KeyError:
        #user is not logged in through spotify if session['token_info'] returns a key error
        return redirect('/login')
    if token_info['access_token'] == None:
        return redirect('/login')
    #if its expired make a new one
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info['access_token'] = sp_oauth.refresh_access_token(token_info['refresh_token'])
    #essentially just returning session[token info] with 2 caveats
    return token_info['access_token']
#page allowing user ot login with spotify
@app.route("/search", methods=["GET","POST"])
def search():
    if request.method == "POST":
        artist = request.form.get("artist")
        token = get_token()
        #query for a new name if the one entered can't be found
        try:
            uri = get_artist_uri(artist, token)
        except TypeError:
            return redirect("/login")
        #store uri in session for use in other functions
        session["uri"] = uri
        session["artist"] = artist
        return redirect("/results")
    #if keying into token info fails, user was directed to search page before logging in, so redirect to login page
    try:
        session["token_info"] == None
    except KeyError:
        return redirect("/login")
    else:
        return render_template("search.html")


@app.route("/results", methods=["GET","POST"])
def results():
    #push button on results to add the 10 songs to a playlist
    if request.method == "POST":
        return redirect("/success")
    #display the results of the search
    else:
        #artist uri
        #if user is logged in but accesses results page before searching, redirect to search page
        try:
            uri = session["uri"]
        except KeyError:
            return redirect("/search")
        token = get_token()
        #list of song uris, song previews, and album cover images
        try:
            uris, previews, covers = get_songs(uri, token)
            uris = [uri[14:] for uri in uris]
            song_names = get_song_names(uris, token)
            name = get_artist_name(uri, token)
            return render_template("results.html",song_names=song_names, previews=previews,covers=covers, name=name,)
        #type error is raised when artist can't be found because get_artist_uri returned None.
        except TypeError:
            return redirect("/search")


@app.route("/success",methods=["GET", "POST"])
def success():
    if request.method == "GET":
        return redirect('/login')
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    token = get_token()
    user_id = get_user_id(token)
    print("##########")
    print(user_id)
    #create playlist and get ID
    uri = session["uri"]
    name = get_artist_name(uri, token)
    playlist_id = create_playlist(user_id, name, token)
    #the uris returned from get_songs are needed to add those songs to playlist
    uris, previews, covers = get_songs(uri, token)
    add_to_playlist(uris, playlist_id, token)
    return render_template("success.html")

@app.route("/about")
def about():
    return render_template("about.html")




