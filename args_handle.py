#!/usr/bin/env python

from optparse import OptionParser
import glob
import os

def getFileAbspath(path):
        """Transform any path to absolutely path.

        Args:
            path: Any path string

        Return:
            A absolute path string

        """
        if path[0] == '~':
            return os.path.expanduser(path)
        else:
            return os.path.abspath(path)

def argsHandle():
    parser = OptionParser(description='Redis slowlog formator', usage='python slowlog_formator.py -i <input_files>')
    parser.add_option('-i', dest='input_files', help='read logs from input_files')
    (opts, args) = parser.parse_args()
    if not opts.input_files:
        parser.error('-i option is required')
    # INPUT_FILES = glob.glob(getFileAbspath(opts.input_files))
    return opts

def do_something():
    # do something
    pass

def main():
    opts = argsHandle()
    input_files = glob.glob(getFileAbspath(opts.input_files))
    print('\n'.join(log_parser(input_files)))

if __name__ == '__main__':
    main()
