import os
import json
import requests

#https://developer.spotify.com/documentation/web-api/reference/#/
#https://developer.spotify.com/console/

def get_user_id(spotify_token):
    endpoint = "https://api.spotify.com/v1/me"
    response = requests.get(
        endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )
    response_json = response.json()
    return response_json['id']

#creates playlist and returns that playlist's id
def create_playlist(user_id, name, spotify_token):
    request_body = json.dumps({
        "name": f"{name}'s top 10",
        "description": f"The current top 10 songs by {name}. Created using JRDN-Toptens",
        "public": True
    })

    endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    response = requests.post(
        endpoint,
        data = request_body,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )

    response_json = response.json()
    print("###########")
    print("This terminal output comes from create_playlist")
    print(response_json)
    #playlist ID
    return response_json["id"]

#get top 10 current drake songs' uris, 30sec preview links, and album cover images
def get_songs(artist_uri, spotify_token):
    #slice string to remove "spotify:artist:"
    artist_id = artist_uri[15:]
    #
    market = 'US'
    endpoint = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market={market}'
    response = requests.get(
        endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )

    # the 10 uris, song previews, and album covers will be stored in 3 separate lists
    uris = []
    previews = []
    covers = []
    response_json = response.json()

    i = 0
    #exception for invalid artists
    try:
        for i in range(10):
            uris.append(response_json['tracks'][i]['uri'])
            previews.append(response_json['tracks'][i]["preview_url"])
            covers.append(response_json['tracks'][i]['album']['images'][0]['url'])
    except IndexError or KeyError:
        return None

    return uris, previews, covers

#add drake songs to playlist
def add_to_playlist(uris, playlist_id, spotify_token):
    endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    #collect uris
    request_body = json.dumps({
        "uris": uris,
        "position": 0
    })
    response = requests.post(
        endpoint,
        data = request_body,
        headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {spotify_token}"
        }
    )
    response_json = response.json()
    return response_json

def get_artist_uri(name, spotify_token):
    endpoint = f"https://api.spotify.com/v1/search?q=artist%3A{name}&type=artist&market=US&limit=50"
    response = requests.get(
        endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )
    response_json = response.json()
    #if user tries to access the search page before authentication, return None
    try:
        artists = response_json["artists"]["items"]
    except KeyError:
        return None
    #if artist can't be found, returns none
    try:
        artist = artists[0]["uri"]
        return artist
    except IndexError:
        return None


def get_song_names(uris, spotify_token):
    market = 'US'
    # '%2C' replaces comma separation in get request
    ids = '%2C'.join(uris)
    endpoint = f"https://api.spotify.com/v1/tracks?market={market}&ids={ids}"
    response = requests.get(
        endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )
    response_json = response.json()
    i = 0
    song_names = []
    for i in range(10):
        song_names.append(response_json['tracks'][i]['name'])
    return song_names

# used for the f string in the name of the playlist/playlist description.  For continuity's sake
# if user types "Drak", the search knows they meant Drake so it returns Drake.
# playlist should always be the name of the artist that's actually in spotify
# rather than a one to one string of the user's query
def get_artist_name(uri, spotify_token):
    id = uri[15:]
    endpoint = f"https://api.spotify.com/v1/artists/{id}"
    response = requests.get(
        endpoint,
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spotify_token}"
        }
    )
    response_json = response.json()
    name = response_json['name']
    return name

