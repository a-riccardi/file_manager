"""
This module contains the MData class, used to associate information with a specific file.

Classes:
    MData
"""

import json
import logging as log
import math
import os
from datetime import datetime

import utils

class MData(object):
    """Class representing arbitrary metadata associated with a file."""

    fpath = None
    fname = None
    m_time = None
    c_time = None
    size = None
    data = {}

    def __init__(self, fpath):
        self.fpath = fpath
        self.fname = os.path.basename(fpath).partition(".")[0]

        self.m_time = None
        self.c_time = None
        self.size = None

        self.get_common_mdata()
        self.load()

    def __str__(self):
        return "MData file for <{}>{} Data:{}".format(self.fpath, "" if self.is_valid else " - INVALID", self.data)

    @property
    def is_valid(self):
        """Perform checks to verify that the file is still valid."""

        return os.path.exists(self.fpath)

    @property
    def creation_time(self):
        """Returns a human-readable string with creation time."""

        if self.c_time:
            return datetime.fromtimestamp(self.c_time).strftime("%A, %B %d, %Y %I:%M:%S")
        else:
            log.error("No creation time available for <{}>".format(self.fpath))
            return ""

    @property
    def last_edit_time(self):
        """Returns a human-readable string with last edit time."""

        if self.m_time:
            return datetime.fromtimestamp(self.m_time).strftime("%A, %B %d, %Y %I:%M:%S")
        else:
            log.error("No creation time available for <{}>".format(self.fpath))
            return ""

    def get_file_size(self, unit):
        """Returns a human-readable string with file size."""

        if not isinstance(unit, int):
            log.error("Invalid unit request! ({}) Please provide a value from utils.FILESIZE enum".format(unit))
            return ""

        return "{:.2f} {}(s)".format(self.size / math.pow(1024, unit), utils.FILESIZE.get_name(unit).capitalize())

    def is_file_mdata(self, fname):
        """"Returns True if this .mdata file is associated with the fname"""

        return self.fname == fname

    def get_common_mdata(self):
        """Extract common data from the associated file object."""

        if not self.is_valid:
            return
        
        self.m_time = os.path.getmtime(self.fpath)
        self.c_time = os.path.getctime(self.fpath)
        self.size = os.path.getsize(self.fpath)

    def add_tags(self, *tags):
        """Adds a list of tags to this mdata. Redundant tags won't be added again."""

        try:
            tag_list = self.data["tags"]
        except KeyError:
            tag_list = []

        tag_list.extend(tags)
        
        self.data["tags"] = list(set(tag_list))

    def remove_tags(self, *tags):
        """Removes a list of tags from this mdata."""

        try:
            tag_list = self.data["tags"]
        except KeyError:
            return

        self.data["tags"] = [t for t in tag_list if t not in tags]

    def filter(self, mode, *tags):
        """Returns True if the mdata tags match the provided tags, based on 'mode'."""

        # compute intersection between this mdata taglist and the filter tags
        intersection = len(set.intersection(set(self.data["tags"]), set(tags)))

        if mode == utils.FILTERMODE.ANY:
            return intersection > 0
        elif mode == utils.FILTERMODE.ALL:
            return intersection == len(tags)
        else:
            log.error("Invalid filter mode specified! ({}) Please provide a value from utils.FILTERMODE enum".format(mode))
            return False

    def save(self):
        """Save this mdata to disk."""

        # generate the .mdata file path
        mdata_path = self.generate_mdata_filepath()

        # write .mdata file to disk
        with open(mdata_path, "w+") as mdata_file:
            try:
                mdata_file.write(self.serialize())
            except IOError as e:
                log.error("Couldn't write metadata at <{}> because {}".format(mdata_path, e))
                return False

        return True

    def load(self):
        """Load a .mdata file from disk."""

        # generate the .mdata file path
        mdata_path = self.generate_mdata_filepath()

        if not os.path.exists(mdata_path):
            return False

        # load .mdata file from disk
        with open(mdata_path, "r") as mdata_file:
            try:
                self.deserialize(mdata_file.read())
                return True
            except IOError as e:
                log.error("Couldn't read metadata at <{}> because {}".format(mdata_path, e))
                return False

    def serialize(self):
        """Returns a json string containing this object metadata for serialization."""

        try:
            return json.dumps(self.data, sort_keys=True, indent=4,
                            separators=(',', ': '))
        except TypeError as t_error:
            log.error("Metadata serialization failed for <{}> - {}".format(
                self.fpath, t_error))
            return ""

    def deserialize(self, data):
        """Loads a json string into the data section of this MData class."""
        
        try:
            self.data = utils.byteify(json.loads(data))
        except ValueError as v_error:
            log.error("Metadata deserialization failed for <{}> - {}".format(
                self.fpath, v_error))

    def generate_mdata_filepath(self):
        """Generate the appropriate .data filepath based on the assigned fpath."""

        # generate .mdata file name and folder
        mdata_name = os.path.basename(self.fpath).partition(".")[0]
        mdata_folder_name = os.path.basename(os.path.dirname(self.fpath))
        mdata_path = os.path.join(os.path.dirname(self.fpath), "{}_mdata".format(mdata_folder_name))
        
        # generate .mdata folder if not existent
        utils.make_dirs_if_not_existent(mdata_path)

        # generate and return proper .mdata file path
        return os.path.join(mdata_path, "{}.mdata".format(mdata_name))