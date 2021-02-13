"""
This module is the entry point for the file_system manager. Run this in a cmd to get
an interactive system to save, edit & query file tags.
"""

from cmd import Cmd

import file_manager

class FileManagerCmd(Cmd, object):
    """Cmd interface for file_system.py"""

    def __init__(self):
        super(FileManagerCmd, self).__init__()

        print "Initializing file_manager."

        file_manager.init()

    def split_args(self, args):
        """Returns the provided args to a func."""

        return args.split(" ")

    def do_save(self, args):
        """Save modifications to .mdata and .dbconfig files."""

        file_manager.save()

    def do_filter(self, args):
        """filter [mode] [tag(s)]
        Returns a list of files matching the provided 'tag(s)' using 'mode'."""

        arglist = self.split_args(args)

        if len(arglist) < 2:
            print "Error: not enough arguments provided! {}. Please provide at least a mode and a tag argument." \
                "type 'help filter' for information about this command".format(arglist)
            return
        
        mode = int(arglist[0])
        tags = arglist[1:]

        flist = file_manager.get_files_for_tags(mode, *tags)

        print [md.fpath for md in flist] if len(flist) > 0 else "No match found for tags {} with mode {}".format(tags, mode)

    def do_set_password(self, args):
        """set_password [old_pw] [new_pw]
        Sets or Updates the current encryption password."""

        arglist = self.split_args(args)
        arglen = len(arglist)

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