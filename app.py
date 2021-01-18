import argparse
import csv
import json
import logging
import urllib.parse
import pywikibot
import requests


class Helper:

    TITLES_API = ("https://www.wikidata.org/w/api.php?action=query"
                  "&titles={}&format=json")

    def __init__(self):
        pass

    def clean_up_string(self, somestring):
        return " ".join(somestring.split()).strip()

    def validate_q(self, qstring, datatype):
        legit_value = False
        if datatype == "string":
            legit_value = True
        if datatype == "wikibase-item":
            item_data = requests.get(self.TITLES_API.format(qstring)).text
            parsed_item_data = json.loads(item_data)
            if "-1" not in parsed_item_data["query"]["pages"]:
                legit_value = True
        return legit_value


def add_caption_json(language, content):
    caption = {
        'language': language,
        'value': content
    }
    return caption


def create_datavalue(value, valuetype):
    if valuetype == "wikibase-item":
        datavalue = {
            'value': {
                'numeric-id': value[1:],
                'id': value,
                'entity-type': 'item'
            },
            'type': 'wikibase-entityid',
        }
    elif valuetype == "string":
        datavalue = {
            'value': value,
            'type': 'string',
        }
    return datavalue


def create_claim_json(pid, value, valuetype):
    datavalue = create_datavalue(value, valuetype)
    newclaim = {
        'mainsnak': {
            'snaktype': 'value',
            'property': pid,
            'datavalue': datavalue,
        },
        'type': 'statement',
        'rank': 'normal',
        'qualifiers-order': [],
        'qualifiers': {}
    }
    return newclaim


def get_current_mediainfo(mediaid):
    """
    Check if the media info exists.
    If that's the case, return that so we can expand it.
    Otherwise return an empty dict
    :param mediaid: The entity ID (like M1234, pageid prefixed with M)
    :return: json
    """
    site = pywikibot.Site('commons', 'commons')
    request = site._simple_request(action='wbgetentities', ids=mediaid)
    data = request.submit()
    if data.get('entities').get(mediaid).get('pageid'):
        return data.get('entities').get(mediaid)
    return {}


def write_caption(json_data, mid, summary):
    site = pywikibot.Site('commons', 'commons')
    token = site.tokens['csrf']
    post_data = {
        'action': 'wbsetlabel',
        'format': 'json',
        'id': mid,
        'value': json_data.get("value"),
        'summary': summary,
        'language': json_data.get("language"),
        'bot': True,
        'token': token,
    }
    request = site._simple_request(**post_data)
    try:
        data = request.submit()
        logging.info("Adding caption in {} : {} {}".format(
            json_data.get("language"), json_data.get("value"), summary))
    except pywikibot.data.api.APIError:
        pywikibot.output(
            'Got an API error while saving page. Sleeping and skipping')


def get_datatype(prop):
    url = ("https://www.wikidata.org/w/api.php?action=wbgetentities"
           "&ids={}&format=json&props=datatype")
    response = json.loads(requests.get(url.format(prop)).text)
    return response["entities"][prop]["datatype"]


def write_statement(json_data, mid, summary):
    site = pywikibot.Site('commons', 'commons')
    token = site.tokens['csrf']
    post_data = {'action': 'wbeditentity',
                 'format': 'json',
                 'id': mid,
                 'data': json.dumps(json_data, separators=(',', ':')),
                 'token': token,
                 'summary': summary,
                 'bot': True,
                 }
    request = site._simple_request(**post_data)
    try:
        data = request.submit()
        logging.info(summary)
    except pywikibot.data.api.APIError:
        pywikibot.output(
            'Got an API error while saving page. Sleeping and skipping')


def read_data(filename):
    datalist = []
    with open(filename, 'r') as data:
        for line in csv.DictReader(data):
            datalist.append(line)
    return datalist


def main(arguments):
    logname = "log.log"
    print("Logging to {}.".format(logname))
    logging.basicConfig(filename=logname,
                        filemode='a',
                        format='%(asctime)s;%(levelname)s;%(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)
    site = pywikibot.Site('commons', 'commons')
    data = read_data(arguments.get("data"))
    custom_editsummary = arguments.get("summary")
    helper = Helper()
    for row in data:
        claims_to_add = {'claims': []}
        filename = row.get("Filename")
        page = pywikibot.Page(site, title='{}'.format(
            urllib.parse.quote(filename)), ns=6)
        mid = 'M' + str(page.pageid)
        mediainfo = get_current_mediainfo(mid)
        mediastatements = mediainfo.get("statements")
        for key in row.keys():
            if key.startswith("Caption|"):
                language = key.split("|")[1]
                content = helper.clean_up_string(row[key])
                json_data = add_caption_json(language, content)
                write_caption(json_data, mid, custom_editsummary)
            elif key.startswith("P"):
                property_with_qualifiers = key.split("|")
                main_property = property_with_qualifiers[0]
                main_value = helper.clean_up_string(row[key]).split("|")[0]

                if not helper.validate_q(main_value,
                                         get_datatype(main_property)):
                    continue

                if not row[key].strip():
                    continue

                qualifier_properties = property_with_qualifiers[1:]
                qualifier_values = row[key].split("|")[1:]

                claim_data = create_claim_json(
                    main_property, main_value,
                    valuetype=get_datatype(main_property))
                if check_if_already_present(mediastatements, claim_data):
                    continue

                if qualifier_properties:
                    qual_dict = {qualifier_properties[i]: qualifier_values[i]
                                 for i in range(
                        len(qualifier_properties))}
                    claim_data = add_qualifiers_to_claim(claim_data, qual_dict)

                claims_to_add["claims"].append(claim_data)
        edit_comment = create_edit_comment(claims_to_add, custom_editsummary)
        write_statement(claims_to_add, mid, edit_comment)


def check_if_already_present(mediastatements, claim_data):
    present = False
    prop = claim_data["mainsnak"]["property"]

    if mediastatements:
        claims_in_file = mediastatements.get(prop)
        if claims_in_file:
            for claim_in_file in claims_in_file:
                in_file = claim_in_file["mainsnak"].get(
                    "datavalue").get("value")
                in_our_data = claim_data["mainsnak"].get(
                    "datavalue").get("value")
                if sorted(in_file) == sorted(in_our_data):
                    present = True
    return present


def create_edit_comment(claims_to_add, custom):
    properties = []
    base = "Adding {}"
    for claim in claims_to_add["claims"]:
        linked_property = "[[:d:Property:{}|{}]]".format(
            claim["mainsnak"]["property"],
            claim["mainsnak"]["property"])
        properties.append(linked_property)
    joined = ', '.join(properties)
    if custom:
        joined = "{} {}".format(joined, custom)
    return base.format(joined)


def add_qualifiers_to_claim(claim_data, qual_dict):
    helper = Helper()
    for prop in qual_dict:
        valuetype = get_datatype(prop)
        if not helper.validate_q(qual_dict[prop], valuetype):
            continue
        datavalue = create_datavalue(qual_dict[prop], valuetype)
        qualifier = [{
            'snaktype': 'value',
            'property': prop,
            'datavalue': datavalue
        }]
        claim_data["qualifiers"][prop] = qualifier
        claim_data["qualifiers-order"].append(prop)
    return claim_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--summary", required=False)
    args = parser.parse_args()
    main(vars(args))
