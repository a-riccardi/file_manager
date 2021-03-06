"""
This module is the entry point for the file_system manager. Run this in a cmd to get
an interactive system to save, edit & query file tags.
"""

import argparse
from cmd import Cmd
import os
import tempfile

import f_manager as file_manager
from file_manager import utils
from file_manager import mdata

class CmdArgparseWrapper(object):
    def __init__(self, parser):
        """Init decorator with an argparse parser to be used in parsing cmd-line options"""
        
        self.parser = parser
        self.help_msg = ""

    def __call__(self, f):
        """Decorate 'f' to parse 'line' and pass options to decorated function"""

        if not self.parser:  # If no parser was passed to the decorator, get it from 'f'
            self.parser = f(None, None, None, True)

        def f_wrapper(*args):
            line = args[1].split()

            try:
                parsed = self.parser.parse_args(line)
            except SystemExit:
                # catch the SystemExit exception to prevent the program from being closed
                return

            f(*args, parsed=parsed)

        f_wrapper.__doc__ = self.__get_help(self.parser)
        return f_wrapper

    @staticmethod
    def __get_help(parser):
        """Get and return help message from 'parser.print_help()'"""

        f = tempfile.SpooledTemporaryFile(max_size=2048)
        parser.print_help(file=f)
        f.seek(0)
        return f.read().rstrip()

class FileManagerCmd(Cmd, object):
    """Cmd interface for file_system.py"""

    file_list = []
    is_dirty = False

    def __init__(self):
        super(FileManagerCmd, self).__init__()

        print "Initializing file_manager."

        file_manager.init()

    def do_save(self, args):
        """Save modifications to .mdata and .dbconfig files."""

        file_manager.save()
        self.is_dirty = False

    __tag_parser = argparse.ArgumentParser(prog="tag")
    __tag_parser.add_argument("path", help="a full path to a file/folder. Use | to indicate spaces in the path")
    __tag_parser.add_argument("mode", choices=["add", "remove"], help="either 'add' (to add the provided tags to the path) " \
                                                                    "or 'remove' (to remove the provided tags to the path)")
    __tag_parser.add_argument("tags", nargs="*", help="a space-separated list of tags")

    @CmdArgparseWrapper(parser=__tag_parser)
    def do_tag(self, args, parsed):
        """
        tag [path] [mode] [tag(s)]
        [path] : a full path to a file/folder. Use | to indicate spaces in the path
        [mode] : either 'add' (to add the provided tags to the path)
                 or 'remove' (to remove the provided tags to the path)
        [tag(s)] : a space-separated list of tags

        Modify tags for a specific file or a whole folder, depending on the provided path
        """

        path = parsed.path.replace("|", " ")
        if not os.path.exists(path):
            print ("Error: provided path does not exists! <{}>. Please provide a valid path.".format(path))
            return
        
        mode = parsed.mode
        if mode == "add":
            mode = utils.TAGMODE.ADD
        elif mode == "remove":
            mode = utils.TAGMODE.REMOVE
        else:
            print("Error: provided mode is invalid! '{}'. Please provide either 'add' or 'remove'.")
            return
        
        tags = parsed.tags

        file_manager.tag(path, mode, *tags)

        self.is_dirty = True

    __filter_parser = argparse.ArgumentParser(prog="filter")
    __filter_parser.add_argument("mode", choices=["all", "any"], help=" either 'all' (to return only files that match all provided tags) " \
                                                                        "or 'any' (to return all files that match any of the provided tags)")
    __filter_parser.add_argument("tags", nargs="*", help="a space-separated list of tags")

    @CmdArgparseWrapper(parser=__filter_parser)
    def do_filter(self, args, parsed):
        """
        filter [mode] [tag(s)]
        [mode] : either 'all' (to return only files that match all provided tags)
                 or 'any' (to return all files that match any of the provided tags)
        [tag(s)] : a space-separated list of tags

        Returns a list of files matching the provided 'tag(s)' using 'mode'.
        """
        
        mode = parsed.mode
        if mode == "all":
            mode = utils.FILTERMODE.ALL
        elif mode == "any":
            mode = utils.FILTERMODE.ANY
        else:
            print("Error: provided mode is invalid! '{}'. Please provide either 'all' or 'any'.".format(mode))
            return
        
        tags = parsed.tags

        flist = file_manager.get_files_for_tags(mode, *tags)
        self.file_list = [md.fpath if isinstance(md, mdata.MData) else md for md in flist]

        print self.file_list if len(self.file_list) > 0 else "No match found for tags {} with mode {}".format(tags, mode)


    def do_open(self, args):
        """
        open 

        Open the first file into the queried file list
        """

        if len(self.file_list) == 0:
            print("No file queried. Create a list of file using 'filter' function")
            return

        os.startfile(self.file_list.pop(0))
    
    __list_mdata_parser = argparse.ArgumentParser(prog="list_mdata")
    __list_mdata_parser.add_argument("-fp", "--folder_path", nargs="?", default=None,
                                    help="a full path to a folder. Use | to indicate spaces in the path")

    @CmdArgparseWrapper(parser=__list_mdata_parser)
    def do_list_mdata(self, args, parsed):
        """
        list_mdata [folder_path]
        [folder_path] : full path to a specific folder to inspect (if empty, all .mdata files will be listed)
        
        Returns a list of all tagged files inside 'folder_path'
        """

        print file_manager.list_mdata(parsed.folder_path)

    __set_password_parser = argparse.ArgumentParser(prog="set_password")
    __set_password_parser.add_argument("-cpw", "--current_pw", nargs="?", default=None,
                                       help=" the current password (this is optional if no password was set)")
    __set_password_parser.add_argument("new_pw", help="the desired password to use for mdata encryption")

    @CmdArgparseWrapper(parser=__set_password_parser)
    def do_set_password(self, args, parsed):
        """
        set_password [current_pw] [new_pw]
        [current_pw] : the current password (this is optional if no password was set)
        [new_pw] : the desired password to use for mdata encryption

        Sets or Updates the current encryption password.
        """

        current_pw = parsed.current_pw
        new_pw = parsed.new_pw

        file_manager.set_dbase_password(current_pw, new_pw)

        self.is_dirty = True

    __init_with_hwID_parser = argparse.ArgumentParser(prog="init_with_hwID")
    __init_with_hwID_parser.add_argument("hardware_id", help=" the old hardware ID with which the config file was encrypted with")

    @CmdArgparseWrapper(parser=__init_with_hwID_parser)
    def do_init_with_hwID(self, args, parsed):
        """
        init_with_hwID [hardware_id]
        [hardware_id] : the old hardware ID with which the config file was encrypted with.

        Re-loads the config file with a bespoke hardware-ID key. Use this function to restore the
        content after hardware modifications
        """

        hw_id = parsed.hardware_id

        file_manager.init(hw_id)

    def do_print_hwID(self, args):
        """
        print_hwID 

        Print this machine Hardware ID
        """

        print file_manager.get_hardware_id()

    def do_quit(self, args):
        """Quits the program."""

        if self.is_dirty:
            self.do_save(args)

        print "Quitting."
        raise SystemExit

def main():
    """Instantiate the FileManagerCmd class and start the main loop"""

    prompt = FileManagerCmd()
    prompt.prompt = '> '
    prompt.cmdloop('file_manager initialized.')

if __name__ == '__main__':
    main()