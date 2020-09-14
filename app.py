import csv
import json
import time
import urllib.parse
import pywikibot

import pywikibot.config2 as config
config.put_throttle = 5

with open('data.csv', 'r') as f:
    data = list(csv.reader(f))

site = pywikibot.Site('commons', 'commons')
site.login()
site.get_tokens('csrf')
repo = site.data_repository()

def add_claim_json(pid, value):
    """
    Add a claim to a mediaid
    :param mediaid: The mediaid to add it to
    :param pid: The property P id (including the P)
    :param value: string value
    :param summary: The summary to add in the edit
    :return: Nothing, edit in place
    """
    toclaim = {
    'claims': [{
        'mainsnak':{
            'snaktype':'value',
            'property':pid,
            'datavalue':{
                'value':value,
                'type':'string',
                }
            },
            'type':'statement',
            'rank':'normal',
            'qualifiers-order': ['P195'],
            'qualifiers':{
                'P195': [{
                    'snaktype':'value',
                    'property':'P195',
                    'datavalue': {
                        'value': {
                            'entity-type': 'item',
                            'numeric-id': 1142142,
                            'id': 'Q1142142',
                        },
                        'type':'wikibase-entityid',
                    }
                }]
            }
        }]
    }
    return toclaim

def getCurrentMediaInfo(mediaid):
    """
    Check if the media info exists. If that's the case, return that so we can expand it.
    Otherwise return an empty dict
    :param mediaid: The entity ID (like M1234, pageid prefixed with M)
    :return: json
    """
    request = site._simple_request(action='wbgetentities', ids=mediaid)
    data = request.submit()
    if data.get(u'entities').get(mediaid).get(u'pageid'):
        return data.get(u'entities').get(mediaid)
    return {}

def write_statement(json_data, mid, summary):
    token = site.tokens['csrf']
    post_data = {'action' : 'wbeditentity',
                'format' : 'json',
                'id' : mid,
                'data' : json.dumps(json_data, separators=(',', ':')),
                'token' : token,
                'summary': summary,
                'bot' : True,
                }
    request = site._simple_request(**post_data)
    print(request)
    try:
        data = request.submit()
    except pywikibot.data.api.APIError:
        pywikibot.output('Got an API error while saving page. Sleeping and skipping')
        time.sleep(60)

for item in data:
    page = pywikibot.Page(site, title='{}'.format(urllib.parse.quote(item[1])), ns=6)
    mid = 'M' + str(page.pageid)
    nm_identifier = item[2]
    current_data = getCurrentMediaInfo(mid)
    if current_data.get('statements'):
        if current_data.get('statements').get('P217'):
            continue
    json_data = add_claim_json('P217', nm_identifier)
    summary = "Adding identifier ID in Nordic Museum collection"
    write_statement(json_data, mid, summary)