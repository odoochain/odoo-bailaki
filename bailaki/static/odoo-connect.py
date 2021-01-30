from xmlrpc import client as xmlrpclib

url = 'http://127.0.0.1:8069'
db = '12.0-icti-nfe-NEWBRANCH020'
username = 'male1'
password = 'male1'
common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
uid = common.login(db, username, password)

partner_id = models.execute_kw(
    db, uid, password, 'res.partner', 'search', [[['user_ids', '=', uid]]],
    {'limit': 1})

type_selection_for_match = models.execute(
    db, uid, password,
    'res.partner.relation.type.selection', 'search', [['name', '=', 'Match']])

type_selection_for_send_likes = models.execute(
    db, uid, password,
    'res.partner.relation.type', 'search', [['name', '=', 'Send Likes']])

[record] = models.execute_kw(
    db, uid, password,
    'res.partner', 'read', [partner_id],
    {'fields': ['name', 'gender', 'referred_friend_ids', 'relation_all_ids']})

referred_friend_ids = record['referred_friend_ids']
relation_all_ids = record['relation_all_ids']

# Get Referred Friends
referred_friends = models.execute_kw(
    db, uid, password,
    'res.partner', 'read', [referred_friend_ids],
    {'fields': ['name', 'gender']})

# Get Matches Relation
relation_matches = models.execute(
    db, uid, password,
    'res.partner.relation.all', 'search_read', [
        ['id', 'in', relation_all_ids],
        ['type_selection_id', '=', type_selection_for_match]],
    ['this_partner_id', 'type_selection_id', 'other_partner_id'])

# Create send relation
create_new_relation = models.execute_kw(
    db, uid, password,
    'res.partner.relation',
    'create',
    [{
        'left_partner_id': partner_id[0],
        'right_partner_id': referred_friend_ids[1],
        'type_id': type_selection_for_send_likes[0],
      }]
)

print(create_new_relation)
print(referred_friends)
print(relation_matches)
