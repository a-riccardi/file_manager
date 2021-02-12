"""
This module contains a number of useful enums for metadata interaction.
To use an eunm, refer to the uppercase variable in this module representing
the instance of the enum.

e.g.:

import utils
print(utils.FILESIZE.GIGABYTE) # should print '3'

Classes:
    FileSize
    FilterMode

Variables:
    FILESIZE
    FILTERMODE
"""
import os
import math
import logging as log

class BaseEnum(object):
    """ Base Class for enums. Should never be instantiated directly - instead subclass it into the desired Enum
    and just add the values as class variables
    """

    def __init__(self):
        """Initialize _values and _value_name_map instance variables with the declared class variables and their values."""

        self._values = [attr for attr in vars(type(self)) if not callable(getattr(type(self), attr)) and not attr.startswith("__")]
        self._value_name_map = { getattr(type(self), v) : v for v in self._values }

    def __str__(self):
        return "{} values: {}".format(type(self).__name__,  self._value_name_map)

    def get_name(self, value):
        """ Returns the variable name for a given 'value'."""

        try:
            return self._value_name_map[value]
        except KeyError:        
            log.error("Invalid value specified! ({}) {}".format(value, self))
            return None

class FileSize(BaseEnum):
    """Enum-like class to enumerate file size types."""
    
    BYTE = 0
    KILOBYTE = 1
    MEGABYTE = 2
    GIGABYTE = 3
    TERABYTE = 4

class FilterMode(BaseEnum):
    """Enum-like class to enumerate tags query mode."""
    
    ANY = 0
    ALL = 1

class FMCoreFiles(BaseEnum):
    """Enum-like class to enumerate application files."""

    DATABASE = 0
    CONFIG = 1

class FType(BaseEnum):
    """Enum-like class to enumerate valida file types for MData initialization."""

    FILE = 0
    MDATA = 1

FILESIZE = FileSize()
FILTERMODE = FilterMode()
FMCOREFILES = FMCoreFiles()
FTYPE = FType()

def make_dirs_if_not_existent(filepath):
    """Create a directory tree if not already existing."""

    if not os.path.exists(filepath):
        os.makedirs(filepath)

def json_decode(input):
    """Transform a string object inside a json file to a proper string object.

    Taken from https://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-from-json/13105359#13105359
    """

    if isinstance(input, dict):
        return {json_decode(key) : json_decode(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [json_decode(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def clamp(val, min, max):
    """Clamp the value between min and max."""

    if val <= min:
        return min
    elif val >= max:
        return max

    return val