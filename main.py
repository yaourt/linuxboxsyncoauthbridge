# Use locally deployed modules by injecting
# then in the sys.path
import sys
sys.path.insert(0, 'libs')

from bottle import Bottle, redirect, request
import bottle
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import urllib
import uuid
import Crypto.Random
import yaml

# Declaring Bottle application,
# GAE takes care of global 'app' var
app = Bottle()
bottle.debug(True)

config = yaml.load(open('oauth.yaml', 'rb'))
client_id = config['client_id']
client_secret = config['client_secret']
redirect_uri = 'http://127.0.0.1:8080/code'


@app.route('/')
def root():
    state = uuid.uuid4().hex
    memcache.set(state, 'NA', time=60)
    redirect_value = urllib.quote(redirect_uri)

    url = "https://www.box.com/api/oauth2/authorize?response_type=code&client_id=%s&state=%s&redirect_uri=%s" % (client_id,  state, redirect_value)

    redirect(url, 302)

@app.route('/code')
def code():
    code = request.query.code
    state = request.query.state

    state_value = memcache.get(state)
    if state_value is None:
        return "Sorry, you need to try again :-("

    url = "https://www.box.com/api/oauth2/token"

    params = {
        'grant_type' : 'authorization_code',
        'code' : code,
        'client_id' : client_id,
        'client_secret' : client_secret,
        'redirect_uri' : redirect_uri,
    }
    payload = urllib.urlencode(params)

    result = urlfetch.fetch(
        url=url,
        payload=payload,
        method=urlfetch.POST,
        deadline=15
    )
    if 200 == result.status_code:
        memcache.add(state, result.content, 60)
    return redirect("oauth://%s" % (state))

@app.route('/token')
def token():
    code = request.query.state
    return code