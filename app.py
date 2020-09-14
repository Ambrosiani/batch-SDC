import mwapi
import mwoauth
import yaml


try:
    with open(os.path.join(__dir__, 'config.yaml')) as config_file:
        app.config.update(yaml.safe_load(config_file))
except FileNotFoundError:
    print('config.yaml file not found, assuming local development setup')
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(64))
    app.secret_key = random_string

if 'oauth' in app.config:
    oauth_config = app.config['oauth']
    consumer_token = mwoauth.ConsumerToken(oauth_config['consumer_key'],
                                           oauth_config['consumer_secret'])
    index_php = 'https://commons.wikimedia.org/w/index.php'


def oauth_callback():
    request_token = mwoauth.RequestToken(**flask.session.pop('oauth_request_token'))
    access_token = mwoauth.complete('https://commons.wikimedia.org/w/index.php', consumer_token, request_token, flask.request.query_string, user_agent=user_agent)
    flask.session['oauth_access_token'] = dict(zip(access_token._fields, access_token))
    return flask.redirect(flask.url_for('index'))


request_token = mwoauth.initiate(index_php, consumer_token, user_agent=user_agent)

media_id = data['entity']
    for item in data['targets']:
        csrf_token = mwapi_auth_session.get(action='query', meta='tokens', type='csrf')['query']['tokens']['csrftoken']

        entity = {
            'entity-type': 'item',
            'numeric-id': item[1:]
        }
        edit = mwapi_auth_session.post(action='wbcreateclaim', entity=media_id, property='P180', snaktype='value', value=json.dumps(entity), token=csrf_token)