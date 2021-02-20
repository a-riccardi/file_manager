"""
This module is the entry point for the file_system manager. Run this in a cmd to get
an interactive system to save, edit & query file tags.
"""

from cmd import Cmd
import os

import file_manager
from file_manager import utils

class FileManagerCmd(Cmd, object):
    """Cmd interface for file_system.py"""

    def __init__(self):
        super(FileManagerCmd, self).__init__()

        print "Initializing file_manager."

        file_manager.init()

    def split_args(self, args):
        """Returns the provided args to a func."""

        arglist = args.split(" ")
        return arglist, len(arglist)

    def do_save(self, args):
        """Save modifications to .mdata and .dbconfig files."""

        file_manager.save()

    def do_tag(self, args):
        """
        tag [path] [mode] [tag(s)]
        [path] : a full path to a file/folder
        [mode] : either 'add' (to add the provided tags to the path)
                 or 'remove' (to remove the provided tags to the path)
        [tag(s)] : a space-separated list of tags

        Modify tags for a specific file or a whole folder, depending on the provided path
        """

        arglist, arglen = self.split_args(args)

        if arglen < 3:
            print("Error: not enough arguments provided! {}. Please provide a path to a file/folder," \
                "add/remove as mode and a list of tags".format(arglist))
            return

        path = arglist[0]
        if not os.path.exists(path):
            print ("Error: provided path does not exists! <{}>. Please provide a valid path.")
            return
        
        mode = arglist[1]
        if mode == "add":
            mode = utils.TAGMODE.ADD
        elif mode == "remove":
            mode = utils.TAGMODE.REMOVE
        else:
            print("Error: provided mode is invalid! '{}'. Please provide either 'add' or 'remove'.")
            return
        
        tags = arglist[2:]

        file_manager.tag(path, mode, *tags)

    def do_filter(self, args):
        """
        filter [mode] [tag(s)]
        [mode] : either 'all' (to return only files that match all provided tags)
                 or 'any' (to return all files that match any of the provided tags)
        [tag(s)] : a space-separated list of tags

        Returns a list of files matching the provided 'tag(s)' using 'mode'.
        """

        arglist, arglen = self.split_args(args)

        if arglen < 2:
            print "Error: not enough arguments provided! {}. Please provide at least a mode and a tag argument." \
                "type 'help filter' for information about this command".format(arglist)
            return
        
        mode = arglist[0]
        if mode == "all":
            mode = utils.FILTERMODE.ALL
        elif mode == "any":
            mode = utils.FILTERMODE.ANY
        else:
            print("Error: provided mode is invalid! '{}'. Please provide either 'all' or 'any'.")
            return
        
        tags = arglist[1:]

        flist = file_manager.get_files_for_tags(mode, *tags)

        print [md.fpath for md in flist] if len(flist) > 0 else "No match found for tags {} with mode {}".format(tags, mode)

    def do_list_mdata(self, args):
        """
        list_mdata [folder_path]
        [folder_path] : full path to a specific folder to inspect (if empty, all .mdata files will be listed)
        
        Returns a list of all tagged files inside 'folder_path'
        """

        arglist, arglen = self.split_args(args)

        if arglen > 1:
            print "Error: too many arguments provided! {}. Please provide a path to a folder to query the tagged file inside," \
                "or leave it empty to list all tagged files on this machine.".format(arglist)

        print file_manager.list_mdata(arglist[0] if arglen > 0 else None)

    def do_set_password(self, args):
        """
        set_password [current_pw] [new_pw]
        [current_pw] : the current password (this is optional if no password was set)
        [new_pw] : the desired password to use for mdata encryption

        Sets or Updates the current encryption password.
        """

        arglist, arglen = self.split_args(args)

        if file_manager.has_pw():
            if arglen != 2:
                print "Error: wrong arguments provided! {}. Please provide the current password and the new password.".format(arglist)
                return
        elif arglen != 1:
            print "Error: wrong enough arguments provided! {}. Please provide the password you wish to encrypt metadata with.".format(arglist)
            return

        current_pw = None if arglen < 2 else arglist[0]
        new_pw = arglist[0 if arglen < 2 else 1]

        file_manager.set_dbase_password(current_pw, new_pw)

    def do_quit(self, args):
        """Quits the program."""

        print "Quitting."
        raise SystemExit

if __name__ == '__main__':
    """Instantiate the FileManagerCmd class and start the main loop"""

    prompt = FileManagerCmd()
    prompt.prompt = '> '
    prompt.cmdloop('file_manager initialized.')