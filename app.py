from flask import Flask, url_for, redirect, request, render_template, session
import requests
import time
import os





app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_NAME'] = os.environ.get('SESSION_COOKIE_NAME')


REDIRECT_URI = os.environ.get('REDIRECT_URI')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
LOGIN_URL = f'https://osu.ppy.sh/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=public'
API_URL = 'https://osu.ppy.sh/api/v2'
AUTH_URL = 'https://osu.ppy.sh/oauth/token'
TOKEN_INFO = 'token_info'
AUTH_HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }





@app.route('/')
@app.route('/home')
def home():
    token_info = auth_validation()
    if token_info == 0:
        return render_template('index.html', token_info=token_info, LOGIN_URL=LOGIN_URL)
    return render_template('index.html', LOGIN_URL=LOGIN_URL)



@app.route('/userpage')
def userpage():
    token_info = auth_validation()
    if token_info == 0:
        return redirect(url_for('home'))
    ### content of the userpage ###
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer ' + token_info['access_token']
    }
    r = requests.get(f'{API_URL}/me/osu', params={'mode': 'osu'}, headers=headers).json()
    user_id = r['id']
    avatar = r['avatar_url']
    username = r['username']
    user_country = r['country']['name']
    r = requests.get(f'{API_URL}/users/{user_id}/scores/best', params={'mode': 'osu', 'limit': '1'}, headers=headers).json()
    beatmap = r[0]['beatmapset']
    beatmap_pp = r[0]['pp']
    return render_template('userpage.html', \
                            avatar=avatar, username=username, user_country=user_country, 
                            beatmap_pp=beatmap_pp, beatmap=beatmap)


@app.route('/callback')
def callback():  
    if request.args.get('code'):
        code = request.args.get('code') 
        access_token = get_access_token(code)
        session[TOKEN_INFO] = access_token
        return redirect(url_for('userpage'))
    else:
        return redirect(url_for('home'))



def get_access_token(code):   
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('callback', _external=True),
        'scope': 'public'
    } 
    response = requests.post(AUTH_URL, data=data, headers=AUTH_HEADERS).json()


    return response   


def auth_validation():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return 0    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': token_info['refresh_token'],
        'access_token': token_info['access_token'],
        'grant_type': 'refresh_token'    
    }
    now = int(time.time())
    is_expired = now - token_info['expires_in'] < 60
    if is_expired:
        r = requests.post(AUTH_URL, data=data, headers=AUTH_HEADERS)

    return token_info




    






if __name__ == '__main__':
    app.run(debug=True)