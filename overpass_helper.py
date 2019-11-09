# Standard python imports
import time
import hashlib
import logging
logger = logging.getLogger('utility_to_osm.overpass_helper')

# This project
import file_util
import overpass_helper

# External dependencies:
import osmapis

osmapis_overpass = osmapis.OverpassAPI()
osmapis_overpass.previous_request = 0#time.time()

def overpass_xml(xml, old_age_days=7, cache_filename=None):
    ''' Query the OverpassAPI with the given xml query, cache result for old_age_days days
    in file cache_filename (defaults to cache_<md5(xml)>.osm)
    '''
    if cache_filename is None:
        filename = 'cache_' + hashlib.md5(xml).hexdigest() + '.osm'
    else:
        filename = cache_filename
    
    cached, outdated = file_util.cached_file(filename, old_age_days=old_age_days)
    if cached is not None and not(outdated):
        logger.info('Using overpass responce stored as "%s". Delete this file if you want an updated version' % filename)
        try:
            return osmapis.OSMnsrid.from_xml(cached)
        except AttributeError:  # 'module' object has no attribute 'OSMnsrid'
            return osmapis.OSM.from_xml(cached)

    time_since_last_request = time.time() - osmapis_overpass.previous_request
    if time_since_last_request < 10:
        logger.debug('backing off overpass for 20 seconds')
        time.sleep(20)
    
    osm = osmapis_overpass.interpreter(xml)
    osmapis_overpass.previous_request = time.time()

    logger.info('Overpass responce stored as %s' % filename)
    osm.save(filename)

    return osm


def get_xml_query(query_template, bounding_box=[3.33984375, 57.468589192089325, 38.408203125, 81.1203884020757],
                  relation_id=2978650, # Mainland norway: relation_id=1059668, Legal norway: relation_id=2978650
                  use='relation', recurse=True):
    if use == 'bounding_box':
        variables_query = ''
        area_query = '<bbox-query into="_" w="{w}" s="{s}" e="{e}" n="{n}" />'.format(w=bounding_box[0],
                                                                                      s=bounding_box[1],
                                                                                      e=bounding_box[2],
                                                                                      n=bounding_box[3])
    elif use == 'relation':
        searchArea_ref = int(relation_id)
        searchArea_ref += 3600000000 # beats me
        variables_query = '<id-query into="searchArea" ref="{ref}" type="area"/>'.format(ref=searchArea_ref)
        area_query = '<area-query from="searchArea" into="_" ref=""/>'
    else:
        raise ValueError('unkown use = "%s"', use)

    recurse_query = ''
    if recurse:
        recurse_query = '''<!-- <recurse from="_" into="_" type="down"/> -->
        <!-- <print e="" from="_" geometry="skeleton" limit="" mode="meta" n="" order="quadtile" s="" w=""/> -->'''

    with open(query_template, 'r') as f:
        query = f.read()
    
    query = query.format(variables_query=variables_query,
                         area_query=area_query,
                         recurse=recurse_query)
    logger.debug('XML query """%s"""', query)
    return query

