#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard python imports
import os
import json
# This project
try:
    import gentle_requests
except:
    from . import gentle_requests
try:
    import overpass_helper
except:
    from . import overpass_helper

request_session = gentle_requests.GentleRequests()

global nr2name, name2nr
nr2name, name2nr = None, None

def get_fylker(cache_dir='data', old_age_days=30):
    url = 'http://barnehagefakta.no/api/Fylker'
    filename = os.path.join(cache_dir, 'fylker.json')
    return request_session.get_cached(url, filename, old_age_days=old_age_days)

def kommunenummer(*args, **kwargs):
    """Returns two dictionaries of kommune-nr (as integer) and kommune-name (as string), 
    the first dictionary has the number as key and the name as value, while the second has the reverse."""
    global nr2name, name2nr
    if nr2name is None or name2nr is None:
        nr2name = dict()
        j = get_fylker(*args, **kwargs)
        d = json.loads(j)
        for fylke in d['fylker']:
            for kommune in fylke['kommuner']:
                nr = int(kommune['kommunenummer'])
                navn = kommune['kommunenavn']
                nr2name[nr] = navn

        name2nr = dict(zip(nr2name.values(),nr2name.keys()))
    #else: use cached
    return nr2name, name2nr

def kommune_fylke(*args, **kwargs):
    """Returns a dictionary with kommune-nr (as integer) is key and (fylke_name, fylke_nr) as the data"""
    kommuneNr_2_fylke = dict()
    j = get_fylker(*args, **kwargs)
    d = json.loads(j)
    for fylke in d['fylker']:
        navn = fylke['fylkesnavn']
        fylke_nr = fylke['fylkesnummer']
        for kommune in fylke['kommuner']:
            nr = int(kommune['kommunenummer'])
            kommuneNr_2_fylke[nr] = (navn, fylke_nr)

    return kommuneNr_2_fylke

def to_kommunenr(arg):
    """Allow flexible format for kommune-name, by either number or name"""
    nr2name, name2nr = kommunenummer()
    try:
        nr = int(arg)
    except ValueError:          # not int
        try:
            nr = name2nr[arg]
        except KeyError:
            raise KeyError('Kommune-name "%s" not recognized' % arg)

#    if not nr in nr2name:
#        raise ValueError('Kommune-nr %s not found in kommunenummer.py, feel free to correct the file' % nr)
    
    return '{0:04d}'.format(nr)

def get_osm_kommune_ids(root_template='', cache_dir='',
                        query_template_filename='query_template_kommune_osm_id.xml',
                        cache_filename='query_kommune_osm_id.xml'):
    """Queries overpass for all kommune in osm, returns a dictionary that maps
    kommune_nr (as int) to osm-relation id (as int)"""
    query_template_filename = os.path.join(root_template, query_template_filename)
    cache_filename = os.path.join(cache_dir, cache_filename)
    
    query = overpass_helper.get_xml_query(query_template_filename,
                                         relation_id=2978650, use='relation')
    osm = overpass_helper.overpass_xml(xml=query, old_age_days=30,
                                       cache_filename=cache_filename)
    kommuneNr_2_relationId = dict()
    for relation_id in osm.relations:
        try:
            ref = osm.relations[relation_id].tags['ref']
            kommuneNr_2_relationId[int(ref)] = int(relation_id)
        except KeyError:
            pass

    # Workaround for Longyearbyen arealplanområde, updated 2019.01.01
    if 2100 not in kommuneNr_2_relationId:
        kommuneNr_2_relationId[2100] = 3245620

    return kommuneNr_2_relationId

    
if __name__ == '__main__':
    nr2name, name2nr = kommunenummer()
    for key in nr2name:
        print(key, nr2name[key])
