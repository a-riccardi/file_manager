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

import argparse
import os
import logging as log
import json
import sys
import uuid
from collections import namedtuple

import mdata
import utils
import security

DBaseEntry = namedtuple("DBaseEntry", ["descriptor", "mdata_list", "dir_mdata"])
DirDescriptor = namedtuple("DirDescriptor", ["dirpath", "dir_uuid"])

DBASE_PATH = r'C:\Program Files\FileManager'
dbase_path = os.path.join(DBASE_PATH, "file_manager.dbase")
config_path = os.path.join(DBASE_PATH, "file_manager.dbconfig")
dir_mdata_path = os.path.join(DBASE_PATH, "dir_mdata")

# folder_dbase is a dict { dirpath : DBaseEntry } to allow bosth storage of
# the mdata_list and of a DirDescriptor for serialization
folder_dbase = {}
config = {}

def init(hid=None):
    """Load the folder database and the config file."""

    global config_path
    global dbase_path

    utils.make_dirs_if_not_existent(DBASE_PATH)

    security.set_manager_hook(sys.modules[__name__])

    if os.path.exists(config_path):
        with open(config_path, "r") as config_file:
            try:
                
                config_file_data = config_file.read()

                if hid:
                    config_file_data = security.xor_string(config_file_data, security.generate_base_key(1024, hid))
                else:
                    config_file_data = security.xor_hid(config_file_data)

                deserialize(config_file_data, utils.FMCOREFILES.CONFIG)
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

    global dbase_path
    global config_path

    dbase_save_result = True
    # write .dbase file to disk
    with open(dbase_path, "w+") as dbase_file:
        try:
            dbase_file.write(serialize(utils.FMCOREFILES.DATABASE))

            for _, db_entry in folder_dbase.items():
                db_entry.dir_mdata.save()

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
    """Returns a json string representation of an object for serialization."""

    global folder_dbase
    global config

    try:
        if fmcorefile == utils.FMCOREFILES.DATABASE:
            return json.dumps([db_entry.descriptor._asdict() for db_entry in folder_dbase.values()], cls=utils.Encoder, sort_keys=False, indent=4,
                            separators=(',', ': '))
        elif fmcorefile == utils.FMCOREFILES.CONFIG:
            return json.dumps(config, sort_keys=False, indent=4,
                            separators=(',', ': '))
        else:
            raise ValueError("Invalid value for fmcorefile: <{}>. Please provide a value from utils.FMCOREFILES".format(fmcorefile))
    except TypeError as t_error:
        log.error("{} serialization failed - {}".format(utils.FMCOREFILES.get_name(fmcorefile).capitalize(), t_error))
        return ""

def deserialize(data, fmcorefile):           
    """Loads a json string into the corresponding object."""

    global dir_mdata_path
    global folder_dbase
    global config

    try:
        if fmcorefile == utils.FMCOREFILES.DATABASE:
            descriptor_list = utils.json_decode(json.loads(data))
            for d_dict in descriptor_list:
                try:
                    # generate a DirDescriptor namedtuple from the deserialized dict
                    # NOTE: the field must be in the same order as the namedtuple declaration
                    dir_desc = DirDescriptor(**d_dict)

                    dir_mdata = mdata.MData(dir_desc.dirpath, autoload=False)
                    dir_mdata.override_save_path(dir_mdata_path, dir_desc.dir_uuid)
                    dir_mdata.load()

                    folder_dbase[dir_desc.dirpath] = DBaseEntry(descriptor=dir_desc, mdata_list=load_folder_mdatas(dir_desc.dirpath), dir_mdata=dir_mdata)
                except KeyError as ke:
                    log.error("Unable to generate database entry from descriptor {}. Exception: {}".format(d_dict, ke))
        elif fmcorefile == utils.FMCOREFILES.CONFIG:
            config = utils.json_decode(json.loads(data))
    except ValueError as v_error:
        log.error("{} deserialization failed for <{}> - {}".format(
            utils.FMCOREFILES.get_name(fmcorefile).capitalize(), dbase_path, v_error))

def load_folder_mdatas(dirpath):
    """Load all .mdata files for this dirpath."""

    mdata_dirpath = os.path.join(dirpath, "_mdata")

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
        folder_mdata = folder_dbase[dirpath].mdata_list
    except KeyError:
        folder_mdata = []

    # generate and save new .mdata file
    mdata_file = mdata.MData(fpath)
    mdata_file.save()

    # add this .mdata to the folder database
    folder_mdata.append(mdata_file)
    try:
        folder_dbase[dirpath].mdata_list = folder_mdata 
    except KeyError:
        generate_dbase_entry(dirpath)

    return mdata_file

def generate_dbase_entry(dirpath):
    """Generate a new entry for the provided dirpath"""

    global folder_dbase
    global dir_mdata_path

    # generate random id for this directory mdata file
    dir_mdata_uuid = uuid.uuid4()

    # create the mdata object for this directory
    dir_mdata = mdata.MData(dirpath, autoload=False)
    dir_mdata.override_save_path(dir_mdata_path, dir_mdata_uuid)
    dir_mdata.load()

    folder_dbase[dirpath] = DBaseEntry(descriptor=DirDescriptor(dirpath=dirpath, dir_uuid=dir_mdata_uuid), mdata_list=[], dir_mdata=dir_mdata)

def get_mdata_for_file(fpath):
    """Retrieve a MData class associated with fpath."""

    global folder_dbase

    # if the provided path is not a file, return
    if not os.path.isfile(fpath):
        log.error("Can't add metadata to a non-existing file")
        return

    # get directory path
    fpath = os.path.abspath(fpath)
    if os.path.isfile(fpath):
        dirpath = os.path.dirname(fpath)
    else:
        dirpath = fpath

    try:
        # get list of mdata for current folder
        folder_mdata = folder_dbase[dirpath].mdata_list
        # get the file name for faster filtering
        fname = os.path.basename(fpath).rpartition(".")[0]
        try:
            # return metadata if already cached, else create new MData
            return [md for md in folder_mdata if md.is_file_mdata(fname)][0]
        except IndexError:
            #log.error("Unable to retrieve .mdata for file at <{}>".format(fpath))
            return create_mdata_for_file(fpath)
    except KeyError:
        return create_mdata_for_file(fpath)

def list_mdata(folder_path):
    """Returns a list of tagged files for the provided 'folder_path'"""

    global folder_dbase

    if folder_path and not os.path.isdir(folder_path):
        log.error("Provided folder_path is not a folder! <{}>!" \
        "Please provide a valid folder, or None to list all tagged files on this machine.".format(folder_path))
        return []

    if folder_path:
        try:
            return [md.fpath for md in folder_dbase[folder_path].mdata_list]
        except KeyError:
            return []
    else:
        return [md.fpath for db_entry in folder_dbase.values() for md in db_entry.mdata_list]

def tag(fpath, mode, *tags):
    """Modify tags for the provided fpath."""
    
    if os.path.isfile(fpath):
        mdata_file = get_mdata_for_file(fpath)

        if mdata_file:
            mdata_file.tag(mode, *tags)
    elif os.path.isdir(fpath):
        if not fpath in folder_dbase.keys():
            generate_dbase_entry(fpath)

        folder_dbase[fpath].dir_mdata.tag(mode, *tags)
    else:
        log.error("Can't modify tags for a non-existing path <{}>".format(fpath))

def get_files_for_tags(mode, *tags):
    """Get a list of paths that match the given tags with the provided mode."""

    global folder_dbase

    matching_mdata = []

    for dirpath, db_entry in folder_dbase.items():
        if db_entry.dir_mdata.filter(mode, *tags):
            # if dir_mdata matches the tags, return all files inside this dirpath
            matching_mdata.extend(os.listdir(dirpath))
        else:
            # else, filter each .mdata file in this directory individually
            for mdata_file in db_entry.mdata_list:
                if mdata_file.filter(mode, *tags):
                    matching_mdata.append(mdata_file)

    return matching_mdata

def set_dbase_password(current_pw, new_pw):
    """Update the current encription password."""

    try:
        if not current_pw == config["pw"]:
            log.error("Wrong password entered - returning.")
            return False
    except KeyError:
        # no password stored - assume it's first initialization
        pass

    # if partial loading of dbase folders is implemented, take care of load and save
    # the unloaded .mdata not to mess with the encription

    config["pw"] = new_pw

    return True

def has_pw():
    """Returns True if a user password has already been set, False otherwise."""

    if config:
        return "pw" in config.keys()
    
    return False

def get_hardware_id():
    """Returns the hardware ID for this machine, to be manually saved by the user"""

    return security.generate_hardware_id()

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
    set_dbase_password("wrong_pw!", "new_pw.")

    # add tags to metadata for fpath, generates them if they don't exists
    tag(fpath, utils.TAGMODE.ADD, "text", "important", "test_tag")

    # get the directory for fpath
    dpath = os.path.dirname(fpath)

    # add tags to the folder in which fpath is contained
    tag(dpath, utils.TAGMODE.ADD, "common_folder_tag", "inherited_tag")

    # filter loaded mdata for given tags
    files = get_files_for_tags(utils.FILTERMODE.ANY, "inherited_tag", "non_existent_tag")

    try:
        os.startfile(files[0].fpath)
    except IndexError:
        log.error("No match found for given tags & mode!")

    # save database
    save()