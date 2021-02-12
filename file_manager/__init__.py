"""
This module represents the manager for the file system. It allows to interact with the
various parts of the system and manipulate .mdata files

e.g.

import file_system as fs

# initialize the system database
fs.init()

# --- interact with the module as you like ---

# save changes to metadata and config
fs.save()
"""

import os
import logging as log
import json
import sys

import mdata
import utils
import security

DBASE_PATH = r'C:\Program Files\FileManager'
dbase_path = os.path.join(DBASE_PATH, "file_manager.dbase")
config_path = os.path.join(DBASE_PATH, "file_manager.dbconfig")

folder_dbase = {}
config = {}

def init():
    """Initialize the folder list."""

    utils.make_dirs_if_not_existent(DBASE_PATH)

    security.set_manager_hook(sys.modules[__name__])

    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            try:
                deserialize(security.xor_hid(config_file.read()), utils.FMCOREFILES.CONFIG)
            except IOError:
                pass

    if os.path.exists(dbase_path):
        with open(dbase_path, "r") as dbase_file:
            try:
                deserialize(dbase_file.read(), utils.FMCOREFILES.DATABASE)
            except IOError:
                pass

def save():
    """Save the database to disk."""

    dbase_save_result = True
    # write .dbase file to disk
    with open(dbase_path, "w+") as dbase_file:
        try:
            dbase_file.write(serialize(utils.FMCOREFILES.DATABASE))
        except IOError as e:
            log.error("Couldn't write dbase at <{}> because {}".format(dbase_path, e))
            dbase_save_result = False

    config_save_result = True
    # write .config file to disk
    with open(config_path, "w+") as config_file:
        try:
            config_file.write(security.xor_hid(serialize(utils.FMCOREFILES.CONFIG)))
        except IOError as e:
            log.error("Couldn't write config at <{}> because {}".format(config_path, e))
            config_save_result = False

    return dbase_save_result and config_save_result

def serialize(fmcorefile):
    """Returns a json string containing the database for serialization."""

    global folder_dbase
    global config

    try:
        if fmcorefile == utils.FMCOREFILES.DATABASE:
            return json.dumps(folder_dbase.keys(), sort_keys=True, indent=4,
                            separators=(',', ': '))
        elif fmcorefile == utils.FMCOREFILES.CONFIG:
            return json.dumps(config, sort_keys=True, indent=4,
                            separators=(',', ': '))
        else:
            raise ValueError("Invalid value for fmcorefile: <{}>. Please provide a value from utils.FMCOREFILES".format(fmcorefile))
    except TypeError as t_error:
        log.error("{} serialization failed - {}".format(utils.FMCOREFILES.get_name(fmcorefile).capitalize(), t_error))
        return ""

def deserialize(data, fmcorefile):           
    """Loads a json string into the folder_dbase."""

    global folder_dbase
    global config

    try:
        if fmcorefile == utils.FMCOREFILES.DATABASE:
            folder_list = utils.json_decode(json.loads(data))
            for f in folder_list:
                folder_dbase[f] = load_folder_mdatas(f)
        elif fmcorefile == utils.FMCOREFILES.CONFIG:
            config = utils.json_decode(json.loads(data))
    except ValueError as v_error:
        log.error("{} deserialization failed for <{}> - {}".format(
            utils.FMCOREFILES.get_name(fmcorefile).capitalize(), dbase_path, v_error))

def load_folder_mdatas(dirpath):
    """Load all .mdata files for this dirpath."""

    mdata_dirpath = os.path.join(dirpath, "{}_mdata".format(os.path.dirname(dirpath)))

    if not os.path.exists(mdata_dirpath):
        return []

    mdatas = []
    for root, _, files in os.walk(mdata_dirpath):
        for mdata_fname in files:
            mdatas.append(mdata.MData(os.path.join(root, mdata_fname), utils.FTYPE.MDATA))

    return mdatas

def create_mdata_for_file(fpath):
    """Create a new .mdata file."""

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
    """Retrieve a MData class associated with fpath."""

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
        # get the file name for faster filtering
        fname = os.path.basename(fpath).rpartition(".")[0]
        try:
            # return metadata if already cached, else create new MData
            return [md for md in folder_mdata if md.is_file_mdata(fname)][0]
        except IndexError:
            log.error("Unable to retrieve .mdata for file at <{}>".format(fpath))
            return create_mdata_for_file(fpath)
    except KeyError:
        return create_mdata_for_file(fpath)

def add_tags_to_file(fpath, *tags):
    """Add tags to a .mdata file."""
  
    if not os.path.isfile(fpath):
        return
    
    mdata_file = get_mdata_for_file(fpath)

    if mdata_file:
        mdata_file.add_tags(*tags)
        mdata_file.save()
    
def remove_tags_from_file(fpath, *tags):
    """Remove tags to a .mdata file."""

    if not os.path.isfile(fpath):
        return

    mdata_file = get_mdata_for_file(fpath)

    if mdata_file:
        mdata_file.remove_tags(*tags)
        mdata_file.save()

def get_files_for_tags(mode, *tags):
    """Get a list of paths that match the given tags with the provided mode."""

    global folder_dbase

    matching_mdata = []

    for _, folder_mdata in folder_dbase.items():
        for mdata_file in folder_mdata:
            if mdata_file.filter(mode, *tags):
                matching_mdata.append(mdata_file)

    return matching_mdata

def set_dbase_password(old_pw, new_pw):
    """Update the current encription password."""

    try:
        if not old_pw == config["pw"]:
            log.error("Wrong password entered - returning.")
            return False
    except KeyError:
        # no password stored - assume it's first initialization
        pass

    # if partial loading of dbase folders is implemented, take care of load and save
    # the unloaded .mdata not to mess with the encription

    config["pw"] = new_pw

    return True

if __name__ == "__main__":
    """Example usage for this module."""

    # example file path 
    fpath = r'C:\test_mdata_file.txt'

    # load the database
    init()

    # set password for encription - if it's the first execution,
    # this will just set the password, otherwise will fail
    set_dbase_password(None, "$up3r$Tr0ngPW!")

    # this will fail because the old password don't match the current one
    set_dbase_password("wrong_pw__", "new_pw.")

    # add tags to metadata for fpath, generates them if they don't exists
    add_tags_to_file(fpath, "text", "important", "test_tag")

    # filter loaded mdata for given tags
    files = get_files_for_tags(utils.FILTERMODE.ANY, "tex", "important")

    try:
        os.startfile(files[0].fpath)
    except IndexError:
        log.error("No match found for given tags & mode!")

    # save database
    save()