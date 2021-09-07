from flask import Flask
import pymongo
import os
from authlib.integrations.flask_client import OAuth

connection_url  = os.getenv("CONNECT_MONGODB") #trae la info de .env
client = pymongo.MongoClient(connection_url) #conecta la base de datos
db = client.get_database('Kwikin') #conecta a la base de datos llamada mongotest

application = app = Flask(__name__, template_folder='templates', static_folder='login_limpio/static')
# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/userinfo/v2/me',
    # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)
