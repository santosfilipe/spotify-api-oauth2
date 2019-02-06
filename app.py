from flask import Flask, request, redirect, g, render_template
import requests
import base64
import urllib.parse
import json
import sys

app = Flask(__name__)

# Spotify endpoints 
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com'
API_VERSION = 'v1'
SPOTIFY_API_URL = '{}/{}'.format(SPOTIFY_API_BASE_URL, API_VERSION)

# Flask server parameters
CLIENT_SIDE_URL = 'http://127.0.0.1'
PORT = 5000
REDIRECT_URI = '{}:{}/callback/q'.format(CLIENT_SIDE_URL, PORT)
SCOPE = 'user-read-currently-playing playlist-modify-public playlist-modify-private'
STATE = ''
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# Get OAuth 2.0 tokens from JSON file 
with open('tokens.json', encoding='utf-8') as tokens_file:
    oauth_tokens_from_json = json.loads(tokens_file.read())

client_token = oauth_tokens_from_json["CLIENT_SECRET"]
client_id = oauth_tokens_from_json["CLIENT_ID"]

# OAuth 2.0 request structure 
oauth2_query_parameters = {
    'response_type': 'code',
    'redirect_uri': REDIRECT_URI,
    'scope': SCOPE,
    'client_id': client_id
}

@app.route('/')
def index():
    url_args = '&'.join(['{}={}'.format(key,urllib.parse.quote(val)) for key,val in oauth2_query_parameters.items()])
    auth_url = '{}/?{}'.format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route('/callback/q')
def callback():

    # Spotify API request payload
    authentication_token = request.args['code']
    code_payload = {
        'grant_type': "authorization_code",
        'code': str(authentication_token),
        'redirect_uri': REDIRECT_URI
    }
    encoded_oauth2_tokens = base64.b64encode('{}:{}'.format(client_id, client_token).encode())
    headers = {'Authorization': 'Basic {}'.format(encoded_oauth2_tokens.decode())}

    # POST request to Spotify API with OAuth 2.0 tokens 
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Get tokens from request response
    response_data = json.loads(post_request.text)
    access_token = response_data['access_token']
    token_type = response_data['token_type']
    expires_in = response_data['expires_in']
    refresh_token = response_data['refresh_token']

    # Access Spotify API data using the OAuth 2.0 user token
    authorization_header = {'Authorization':'Bearer {}'.format(access_token)}

    # Get profile data from the Spotify API
    user_profile_api_endpoint = '{}/me'.format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data from the Spotify API
    playlist_api_endpoint = '{}/playlists'.format(profile_data['href'])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)
    
    # Combine profile and playlist data to display
    display_arr = [profile_data] + playlist_data['items']
    return render_template('index.html', sorted_array=display_arr)

if __name__ == '__main__':
    app.run(port=PORT, debug=True)
