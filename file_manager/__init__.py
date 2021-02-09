import os
import logging as log
import json

import mdata
import utils

DBASE_PATH = r'C:\Program Files\FileManager'
dbase_path = os.path.join(DBASE_PATH, "file_manager.dbase")

folder_dbase = {}

def init():
    """Initialize the folder list"""

    utils.make_dirs_if_not_existent(DBASE_PATH)

    if not os.path.exists(dbase_path):
        return

    with open(dbase_path, "r") as dbase_file:
        try:
            deserialize(dbase_file.read())
        except IOError:
            pass

def save():
    """Save the database to disk"""

    # write .dbase file to disk
    with open(dbase_path, "w+") as dbase_file:
        try:
            dbase_file.write(serialize())
        except IOError as e:
            log.error("Couldn't write dbase at <{}> because {}".format(dbase_path, e))
            return False

    return True

def serialize():
    """Returns a json string containing the database for serialization"""

    try:
        return json.dumps(folder_dbase.keys(), sort_keys=True, indent=4,
                        separators=(',', ': '))
    except TypeError as t_error:
        log.error("Database serialization failed - {}".format(t_error))
        return ""

def deserialize(data):           
    """Loads a json string into the folder_dbase"""

    global folder_dbase

    try:
        folder_list = json.loads(data)
        for f in folder_list:
            folder_dbase[f] = load_folder_mdatas(f)
    except ValueError as v_error:
        log.error("Database deserialization failed for <{}> - {}".format(
            dbase_path, v_error))

def load_folder_mdatas(dirpath):
    """Load all .mdata files for this dirpath"""

    mdata_dirpath = os.path.join(dirpath, "{}.mdata".format(os.path.dirname(dirpath)))

    if not os.path.exists(mdata_dirpath):
        return []

    mdatas = []
    for root, dirs, files in os.walk(mdata_dirpath):
        for mdata_fname in files:
            mdatas.append(mdata.MData(os.path.join(root, mdata_fname)))

    return mdatas

def create_mdata_for_file(fpath):
    """Create a new .mdata file"""

    global folder_dbase

    # get directory path
    fpath = os.path.abspath(fpath)
    dirpath = os.path.dirname(fpath)

    # ensure directoy exists
    utils.make_dirs_if_not_existent(dirpath)

    # get .mdata files for this folder 
    try:
        folder_mdata = folder_dbase[dirpath]
    except KeyError:
        folder_mdata = []

    # generate and save new .mdata file
    mdata_file = mdata.MData(fpath)
    mdata_file.save()

    # add this .mdata to the folder database
    folder_mdata.append(mdata_file)
    folder_dbase[dirpath] = folder_mdata 

    return mdata_file

def get_mdata_for_file(fpath):
    """Retrieve a MData class associated with fpath"""

    global folder_dbase

    # if the provided path is not a file, return
    if not os.path.isfile(fpath):
        log.error("Can't add metadata to a non-existing file")
        return

    # get directory path
    fpath = os.path.abspath(fpath)
    dirpath = os.path.dirname(fpath)


    try:
        # get list of mdata for current folder
        folder_mdata = folder_dbase[dirpath]
        try:
            # return metadata if already cached, else create new MData
            return [md for md in folder_mdata if md.is_file_mdata(fpath)][0]
        except IndexError:
            log.error("Unable to retrieve .mdata for file at <{}>".format(fpath))
            return create_mdata_for_file(fpath)
    except KeyError:
        return create_mdata_for_file(fpath)

def add_tags_to_file(fpath, *tags):
    """Add tags to a .mdata file"""
  
    if not os.path.isfile(fpath):
        return
    
    mdata_file = get_mdata_for_file(fpath)

    if mdata_file:
        mdata_file.add_tags(*tags)
        mdata_file.save()
    
def remove_tags_from_file(fpath, *tags):
    """Remove tags to a .mdata file"""

    if not os.path.isfile(fpath):
        return

    mdata_file = get_mdata_for_file(fpath)

    if mdata_file:
        mdata_file.remove_tags(*tags)
        mdata_file.save()

if __name__ == "__main__":

    """Example usage for this module"""

    # example file path 
    fpath = r'C:\test_mdata_file.txt'

    # load the database
    init()

    # add tags to metadata for fpath, generates them if they don't exists
    add_tags_to_file(fpath, "text", "important", "test_tag")

    # save database
    save()