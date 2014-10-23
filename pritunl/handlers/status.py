from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import settings
from pritunl import server
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import __version__

@app.app.route('/status', methods=['GET'])
@auth.session_auth
def status_get():
    server_collection = mongo.get_collection('servers')

    response = server_collection.aggregate([
        {'$project': {
            'client': '$instances.clients',
        }},
        {'$unwind': '$client'},
        {'$unwind': '$client'},
        {'$match': {
            'client.ignore': False,
        }},
        {'$group': {
            '_id': None,
            'clients': {'$addToSet': '$client.id'},
        }},
    ])['result']

    if response:
        users_online = len(response[0]['clients'])
    else:
        users_online = 0

    response = server_collection.aggregate([
        {'$project': {
            '_id': True,
            'status': True,
        }},
        {'$group': {
            '_id': None,
            'servers_count': {'$sum': 1},
            'servers_online': {'$sum': {'$cond': {
                'if': {'$eq': ['$status', True]},
                'then': 1,
                'else': 0,
            }}},
            'servers': {
                '$push': '$status',
            }
        }},
    ])['result']

    if response:
        servers_count = response[0]['servers_count']
        servers_online_count = response[0]['servers_online']
    else:
        servers_count = 0
        servers_online_count = 0

    user_count = organization.get_user_count_multi()
    local_networks = utils.get_local_networks()

    if settings.local.openssl_heartbleed:
        notification = 'You are running an outdated version of openssl ' + \
            'containting the heartbleed bug. This could allow an attacker ' + \
            'to compromise your server. Please upgrade your openssl ' + \
            'package and restart the pritunl service.'
    else:
        notification = settings.local.notification

    return utils.jsonify({
        'org_count': orgs_count,
        'users_online': clients_count,
        'user_count': user_count,
        'servers_online': servers_online_count,
        'server_count': servers_count,
        'server_version': __version__,
        'current_host': settings.local.host_id,
        'public_ip': settings.local.public_ip,
        'local_networks': local_networks,
        'notification': notification,
    })
