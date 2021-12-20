# Standard python imports
import os
import time
import datetime
import logging
logger = logging.getLogger('utility_to_osm.gentle_requests')

# lets try this instead
from urllib.request import urlretrieve

# Non-standard imports
import requests
# This project
try:
    import file_util
except:
    from . import file_util

class GentleRequests(requests.Session):
    """Wrapper around the requests library that inserts a delay to avoid
    excessive load on the server.
    NOTE: currently only wraps get() and post() calls"""
    def __init__(self, N_delay=10, delay_seconds=30, retry_connection_error_hours=1,
                 info = 'Barnehagefakta to Openstreetmap (https://github.com/obtitus/barnehagefakta_osm) '):
        """For every N_delay requests, delay by delay_seconds, if connection failure, retry for retry_connection_error_hours"""
        self.N_delay = N_delay
        self.delay_seconds = delay_seconds
        self.previous_request = None
        self.request_counter = 0
        self.retry_connection_error_hours = retry_connection_error_hours
        
        super(GentleRequests, self).__init__()
        
        self.headers['User-Agent'] = info + self.headers['User-Agent']

    def get(self, *args, **kwargs):
        return self.wrapper(super(GentleRequests, self).get,
                            *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.wrapper(super(GentleRequests, self).post,
                            *args, **kwargs)
    
    def wrapper(self, callback, url, *args, **kwargs):
        # ugly? yes, over-complicated? yes, wierd? definitely
        if self.request_counter == 0:
            self.previous_request = time.time()
        elif self.request_counter >= self.N_delay:
            sleep_time = self.delay_seconds - (time.time() - self.previous_request)
            self.request_counter = -1
            if sleep_time > 0:
                logger.info('Sleeping request for %g seconds...', sleep_time)
                time.sleep(sleep_time)
                
        self.request_counter += 1

        # now retry until we do not get a ConnectionError
        first_request = time.time()
        delta = 0
        while delta < 3600*self.retry_connection_error_hours:
            try:
                return callback(url, *args, **kwargs)
            except (requests.ConnectionError, requests.ReadTimeout, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError) as e:
                delta = time.time() - first_request

                # decide on severity:
                logger_lvl = logging.DEBUG
                if delta > 60:
                    logger_lvl = logging.INFO
                if delta > 60*5:
                    logger_lvl = logging.WARNING
                if delta > 60*60:
                    logger_lvl = logging.ERROR
                # log
                logger.log(logger_lvl, 'Could not connect to %s, trying again in %s: %s',
                           url, datetime.timedelta(seconds=delta), e)
                # linear backoff
                time.sleep(delta)

        # try a last time
        return callback(url, *args, **kwargs)

    def get_cached(self, url, cache_filename, old_age_days=30, **kwargs):
        return self.wrapper_cached(self.get, url, cache_filename,
                                   old_age_days=old_age_days, timeout=60, **kwargs)

    def post_cached(self, url, cache_filename, old_age_days=30, **kwargs):
        return self.wrapper_cached(self.post, url, cache_filename,
                                   old_age_days=old_age_days, timeout=60, **kwargs)
    
    def wrapper_cached(self, callback, url, cache_filename, old_age_days=30, **kwargs):
        cached, outdated = file_util.cached_file(cache_filename, old_age_days)
        if cached is not None and not(outdated):
            #logger.info('returning cached %s %s', cached is not None, not(outdated))
            return cached

        # Hmm, getting some half-downloaded files with requests library, lets try urllib instead
        try:
            urlretrieve(url, cache_filename)
        except Exception as e:
            try: os.remove(cache_filename) # ensure we don't have a half finished download
            except: pass
            logger.error('Failure downloading %s, %s', url, e)
            return None
            
        return file_util.read_file(cache_filename)
        
        # try:
        #     r = callback(url, **kwargs) #self.get(url, **kwargs)
        # except requests.ConnectionError as e:
        #     logger.error('Could not connect to %s, try again later? %s', url, e)
        #     return None

        # logger.info('requested %s %s, got %s', url, cache_filename, r)
        # if r.status_code == 200:
        #     ret = r.content
        #     file_util.write_file(cache_filename, ret)
        #     return ret
        # else:
        #     logger.error('Invalid status code %s', r.status_code)
        #     return None
