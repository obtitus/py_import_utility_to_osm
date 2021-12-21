''' Utility file functions'''
import os
import time
import shutil

import logging
logger = logging.getLogger('utility_to_osm.file_util')

import codecs
def open_utf8(filename, *args, **kwargs):
    logger.debug('open(%s, %s, %s)', filename, args, kwargs)
    return codecs.open(filename, *args, encoding="utf-8-sig", **kwargs)

def rename_file(filename, append):
    """Rename the file by appending, append (while keeping the file-extension). 
    IOError is raised if this would cause an overwrite."""
    name, ext = os.path.splitext(filename)
    new_filename = name + append + ext
    if os.path.exists(new_filename):
        raise IOError('Filename "%s" already exists', filename)
    logger.info('Renaming "%s" -> "%s"', filename, new_filename)
    
    shutil.move(filename, new_filename)

def create_dirname(filename):
    """Given a filename, assures the directory exist"""
    dirname = os.path.dirname(filename)
    if dirname != '' and not(os.path.exists(dirname)):
        os.mkdir(dirname)
    return filename

def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        return f.read()

def write_file(filename, content, mode='w'):
    """Write content to filename, tries to create dirname if the folder does not exist."""
    create_dirname(filename)
    with open(filename, 'w') as f:
        try:
            return f.write(content)
        except:
            return f.write(content.decode())

def file_age(filename):
    fileChanged = os.path.getmtime(filename)
    now = time.time()
    age = (now - fileChanged)/(60*60*24) # age of file in days
    logger.info('file_age(%s) -> %.1f days', filename, age)
    return age

def folder_modification(folder):
    """Returns last modification to any file recursively inside folder as seconds since epoch.
    Returns -1 if the folder is empty"""

    # Not identical to?:
    #time.ctime(max(os.path.getmtime(root) for root,_,_ in os.walk('/tmp/x')))
    
    last_mod = -1
    for root, dirs, files in os.walk(folder):
        for f in files:
            m = os.path.getmtime(os.path.join(root, f))
            last_mod = max(last_mod, m)
    
    return last_mod

def cached_file(filename, old_age_days, mode='r'):
    """ Returns: (content, outdated)
    Returns a tuple of file content (if the file exists) 
    and a boolean for file age older than old_age_days.
    If the file does not exists, (None, False) is returned.
    """
    if os.path.exists(filename):
        age = file_age(filename)
        content = read_file(filename, mode=mode)
        return content, age > old_age_days
    else:
        return None, True

def sanitize_filename(s):
    """replaces all funny characters with _"""
    return "".join([x if x.isalnum() else "_" for x in s])
