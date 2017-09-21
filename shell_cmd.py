#!/usr/bin/env python

import sys
import os
import commands
import logging
import shutil

class BasicCmd(object):
    """Basic class of basic commands

    This class provide basic commands for other class,
    such as 'cd', 'mv', and so on.

    Attributes:
        __init__: Initial the class, it create tow logging handler,
            one for console(info level), one for file(debug level).
        getFileAbspath: Transform any path to absolutely path.
        ls: List files, like 'ls' command on linux.
        cd: Change work path, like 'cd' command on linux.
        mv: Move files, like 'mv' command on linux.
        cp: Copy files, the same as 'cp -a' command on linux.
        rmfile: Remove one file, like 'rm -f' command on linux.
        rmdir: Remove one dir, like 'rm -rf' command on linux.
        mkdir: Make dir, like 'mkdir -p' command on linux.
        pathSplit: Split path to four part.
        sh: Run linux command, like 'sh' command on linux.
        tarZX: Extract file, like 'tar -zxf' command on linux.
        tarZC: Compress files, like 'tar -zcf' command on linux.
        ln: Create symbol link, like 'ln -s' command on linux.
        diff: Compare files, like 'diff' command on linux.

    """
    def __init__(self, log_file):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        console_handler.setFormatter(console_handler_formatter)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(funcName)s[%(lineno)d] - %(message)s')
        file_handler.setFormatter(file_handler_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def getFileAbspath(self, path):
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

    def ls(self, path):
        """List files, like 'ls' command on linux.

        Args:
            path: A dir path

        Return:
            A list of files in the path

        """
        self.logger.debug('os.listdir(%r)' % path)
        path_list = os.listdir(path)
        self.logger.debug('Return: %r' % path_list)
        return path_list

    def cd(self, path):
        """Change work path, like 'cd' command on linux.

        Args:
            path: Any path would be changed to

        """
        self.logger.debug('os.chdir(%r)' % path)
        os.chdir(path)

    def mv(self, src, dst):
        """Move files, like 'mv' command on linux.

        Args:
            src: path of source
            dst: path of destination

        """
        self.logger.debug('shutil.move(%r, %r)' % (src, dst))
        shutil.move(src, dst)

    def cp(self, src, dst):
        """Copy files, the same as 'cp -a' command on linux.

        Args:
            src: path of source
            dst: path of destination

            Because command is 'cp -a', the src can be include
            several path separated by space

        """
        cmd = 'cp -a %s %s' % (src, dst)
        self.logger.debug(cmd)
        result = commands.getoutput(cmd)
        if result:
            raise Exception(result)

    def rmfile(self, path):
        """Remove one file, like 'rm -f' command on linux.

        Args:
            path: Any path of file to be deleted

        """
        if os.path.exists(path):
            self.logger.debug('os.remove(%r)' % path)
            os.remove(path)

    def rmdir(self, path):
        """Remove one dir, like 'rm -rf' command on linux.

        Existing path will be deleted only.

        Args:
            path: Any path of dir to be deleted

        """
        if os.path.exists(path):
            self.logger.debug('shutil.rmtree(%r)' % path)
            shutil.rmtree(path)

    def mkdir(self, path):
        """Make dir, like 'mkdir -p' command on linux.

        If the path not exists, then create.

        Args:
            path: Any path of dir to be create

        """
        if not os.path.exists(path):
            self.logger.debug('os.makedirs(%r)' % path)
            os.makedirs(path)

    def pathSplit(self, path):
        """Split path to four part.

        Split the path to get $dir_name/$file_name and $root$ext
        $dir_name/$file_name == $root$ext

        Args:
            path: Any absolute path to be split

        Return:
            A dic of four parts include dir_name file_name root ext

            {'dir_name': dir_name, 'file_name': file_name, 'root': root, 'ext': ext}

        """
        self.logger.debug('os.path.split(%r)' % path)
        dir_name, file_name = os.path.split(path)
        self.logger.debug('os.path.splitext(%r)' % path)
        root, ext = os.path.splitext(path)
        name = {'dir_name': dir_name, 'file_name': file_name, 'root': root, 'ext': ext}
        self.logger.debug("Return: %r" % name)
        return name

    def sh(self, cmd, no_output=False):
        """Run linux command, like 'sh' command on linux.

        Run the command in shell, get the result or not.

        Args:
            cmd: String of any command
            no_output: Determin whether get the output of the cmd or not

        Return:
            If no_output=False, then get the output return from cmd
            Else, get the status code return from cmd

        """
        result = None
        if no_output:
            self.logger.debug('os.system(%r)' % cmd)
            result = os.system(cmd)
        else:
            self.logger.debug('commands.getoutput(%r)' % cmd)
            result = commands.getoutput(cmd)
        return result

    def tarZX(self, file_name, dst_path='.'):
        """Extract file, like 'tar -zxf' command on linux.

        Run 'tar' command in subshell, extract the tar.gz file.

        Args:
            file_name: The name of tar file
            dst_path: Destinate path extracted to

        Result:
            Any messages while running the command

        """
        cmd = 'tar -zxf %s -C %s > /dev/null' % (file_name, dst_path)
        self.logger.debug(cmd)
        result = commands.getoutput(cmd)
        if result:
            self.logger.warning('Return:\n%s' % result)
        return result
        
    def tarZC(self, file_name, src_path):
        """Compress files, like 'tar -zcf' command on linux.

        Run 'tar' command in subshell, make the tar.gz file.

        Args:
            file_name: The tar.gz file name to be made
            src_path: A path list to be Compress

        Return:
            Any messages while running the command

        """
        src_path_list = []
        for each_path in src_path:
            if os.path.exists(each_path):
                src_path_list.append(each_path)
            else:
                self.logger.warning('<font color=orange><b>tar: %r: Cannot stat: No such file or directory. Skip it.</b></font>' % each_path)
        cmd = 'tar -zcf %s %s > /dev/null' % (file_name, ' '.join(src_path_list))
        self.logger.debug(cmd)
        result = commands.getoutput(cmd)
        if result:
            self.logger.warning('Return:\n%s' % result)
        return result

    def ln(self, src_path, dst_path):
        """Create symbol link, like 'ln -s' command on linux.

        Create a symbol link, if a existed symbol link had the same name,
        will delete it first, then create.

        Args:
            src_path: Source file or path
            dst_path: File name of symbol link

        """
        if os.path.lexists(dst_path):
            self.logger.debug('os.remove(%r)' % dst_path)
            os.remove(dst_path)
        self.logger.debug('os.symlink(%r, %r)' % (src_path, dst_path))
        os.symlink(src_path, dst_path)

    def diff(self, new, old):
        """Compare files, like 'diff' command on linux.

        Compare files, it will print some messages if the file name not exists
        in the 'new' argument or in the 'old' argument or both.

        Args:
            new: A path of new file
            old: A path of old file

        """
        if os.path.exists(new) and not os.path.exists(old):
            self.logger.warning('<font color=orange><b>Only exists %r</b></font>' % new)
        elif not os.path.exists(new) and os.path.exists(old):
            self.logger.warning('<font color=orange><b>Only exists %r</b></font>' % old)
        elif not os.path.exists(new) and not os.path.exists(old):
            self.logger.warning('<font color=orange><b>Both not exists %r %r</b></font>' % (new, old))
        else:
            cmd = 'diff --report-identical-files %s %s' % (new, old)
            self.logger.debug(cmd)
            self.logger.info('%s BEGIN %s\n<font color=green><< New: %r\n>> Old: %r</font>\n<b>%s</b>' % ('='*10, '='*10, new, old, commands.getoutput(cmd)))
            self.logger.info('%s END %s' % ('='*10, '='*10))
