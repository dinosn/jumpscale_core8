from JumpScale import j
from stat import *
import brotli
import hashlib
import functools
import subprocess
import pwd
import grp
import os
import sys
import re


class FListFactory(object):

    def __init__(self):
        self.__jslocation__ = "j.tools.flist"

    def get_flist(self):
        """
        Return a Flist object
        """
        return FList()

    def get_archiver(self):
        """
        Return a FListArchiver object

        This is used to push flist to IPFS
        """
        return FListArchiver()


class FList(object):
    """
        FList (sometime "plist") files contains a plain/text representation of
    a complete file system tree

        FList stand for "file list" (plist for "path list"), this format is made
    for mapping a file with his md5 hash, which allow to retreive file remotly
    and get it's metadata separatly

        FList is formatted to support POSIX ACL, File type representation and
    extra data (can be any type but it's used internaly to describe some file-type)

        A flist file contains one entry per file, fields are separated by "|".
    Filename should not contains the pipe character in it's name otherwise it will
    not be supported at all.

        This is a flist file format supported by this library:
    filepath|hash|filesize|uname|gname|permissions|filetype|ctime|mtime|extended

        - filepath: the complete file path on the filesystem
        - hash: md5 checksum of the file
          - if the file is a special file (block, sylink, ...), use this hash:
            md5("flist:" + filename (fullpath) + ":" + mtime)
        - filesize: size in bytes

        - uname: username owner of the file (used for permissions)
          - note: if username doesn't match any userid, userid will be used
        - gname: groupname owner of the file (used for permissions)
          - note: if groupname doesn't match any groupid, groupid will be used

        - permissions: octal representation of the posix permissions
        - filetype: integer representing the file type:
          - 0: socket       (S_IFSOCK)
          - 1: symlink      (S_IFLNK)
          - 2: regular file (S_IFREG)
          - 3: block device (S_IFBLK)
          - 4: directory    (S_IFDIR) (used for empty directory)
          - 5: char. device (S_IFCHR)
          - 6: fifo pipe    (S_IFIFO)

        - ctime: unix timestamp of the creation time
        - mtime: unix timestamp of the modification file

        - extended: optional field which may contains extra-data related to
          to file type:
          - symlink     : contains the target of the link
          - block device: ...
          - char. device: ...

    """

    def __init__(self):
        self._data = []
        self._hash = {}
        self._path = {}

    def parse(self, filename):
        del self._data[:]
        self._hash.clear()
        self._path.clear()

        index = 0

        with open(filename) as flist:
            for line in flist:
                f = line.strip().split('|')

                index = self._indexForPath(f[1])

                self._data[index] = [
                    f[0],        # path
                    f[1],        # hash
                    int(f[2]),   # size
                    f[3],        # uname
                    f[4],        # gname
                    f[5],        # permission
                    int(f[6]),   # filetype
                    int(f[7]),   # ctime
                    int(f[8]),   # mtime
                    f[9]         # extended
                ]

        return index

    """
    Getters
    """

    def _indexsFromHash(self, hash):
        if hash not in self._hash:
            return None

        return self._hash[hash]

    def getHashList(self):
        hashes = []

        for x in self._data:
            hashes.append(x[1])

        return hashes

    def filesFromHash(self, hash):
        paths = []
        ids = self._indexsFromHash(hash)

        # adding paths from ids list
        for x in ids:
            paths.append(self._data[x][0])

        return paths

    def _getItem(self, filename, index):
        id = self._path[filename]
        if id is not None:
            return self._data[id][index]

        return None

    def getHash(self, filename):
        return self._getItem(filename, 1)

    def getType(self, filename):
        type = self._getItem(filename, 0)
        if type is None:
            return None

        # FIXME

        return None

    def isRegular(self, filename):
        return self._getItem(filename, 6) == 2

    def getSize(self, filename):
        return self._getItem(filename, 2)

    def getMode(self, filename):
        return self._getItem(filename, 5)

    def getOwner(self, filename):
        return self._getItem(filename, 3)

    def getGroup(self, filename):
        return self._getItem(filename, 4)

    def getExtended(self, filename):
        # return self._getItem(filename, 0)
        return -1

    def getCreationTime(self, filename):
        return self._getItem(filename, 7)

    def getModificationTime(self, filename):
        return self._getItem(filename, 8)

    """
    Setters
    """

    def _indexForPath(self, filename):
        if filename not in self._path:
            # creating new entry
            self._data.append([None] * 10)
            id = len(self._data) - 1
            self._data[id][0] = filename
            self._path[filename] = id

        return self._path[filename]

    def _setItem(self, filename, value, index):
        id = self._indexForPath(filename)
        if id is None:
            return None

        self._data[id][index] = value
        return value

    def setHash(self, filename, value):
        self._setItem(filename, value, 1)

        # updating hash list
        id = self._indexForPath(filename)

        if value in self._hash:
            self._hash[value].append(id)

        else:
            self._hash[value] = [id]

        return value

    def setType(self, filename, value):
        # testing regular first, it will probably be
        # the most often used type
        if S_ISREG(value):
            return self._setItem(filename, 2, 6)

        # testing special files type
        if S_ISSOCK(value):
            return self._setItem(filename, 0, 6)

        if S_ISLNK(value):
            return self._setItem(filename, 1, 6)

        if S_ISBLK(value):
            return self._setItem(filename, 3, 6)

        if S_ISCHR(value):
            return self._setItem(filename, 5, 6)

        if S_ISFIFO(value):
            return self._setItem(filename, 6, 6)

        # keep track of empty directories
        if S_ISDIR(value):
            return self._setItem(filename, 4, 6)

        return None

    def setSize(self, filename, value):
        return self._setItem(filename, value, 2)

    def setMode(self, filename, value):
        return self._setItem(filename, value, 5)

    def setOwner(self, filename, value):
        return self._setItem(filename, value, 3)

    def setGroup(self, filename, value):
        return self._setItem(filename, value, 4)

    def setExtended(self, filename, value):
        """
        value: need to be a stat struct
        """
        path = self._getItem(filename, 0)

        # symlink
        if S_ISLNK(value.st_mode):
            xtd = os.readlink(path)
            return self._setItem(filename, xtd, 9)

        # block device
        if S_ISBLK(value.st_mode) or S_ISCHR(value.st_mode):
            id = '%d,%d' % (os.major(value.st_rdev), os.minor(value.st_rdev))
            return self._setItem(filename, id, 9)

        return self._setItem(filename, "", 9)

    def setModificationTime(self, filename, value):
        return self._setItem(filename, int(value), 7)

    def setCreationTime(self, filename, value):
        return self._setItem(filename, int(value), 8)

    """
    Builder
    """

    def _build(self, filename):
        stat = os.stat(filename, follow_symlinks=False)
        mode = oct(stat.st_mode)[4:]

        # grab username from userid, if not found, use userid
        try:
            uname = pwd.getpwuid(stat.st_uid).pw_name
        except:
            uname = stat.st_uid

        # grab groupname from groupid, if not found, use groupid
        try:
            gname = grp.getgrgid(stat.st_gid).gr_name
        except:
            gname = stat.st_gid

        # compute hash only if it's a regular file, otherwise, comute filename hash
        # the hash is used to access the file "id" in the list, we cannot have empty hash
        if not S_ISREG(stat.st_mode):
            hashstr = "flist:%s:%d" % (filename, stat.st_mtime)
            hash = j.data.hash.md5_string(hashstr)

        else:
            hash = j.data.hash.md5(filename)

        self.setHash(filename, hash)
        self.setType(filename, stat.st_mode)
        self.setSize(filename, stat.st_size)
        self.setMode(filename, mode)
        self.setOwner(filename, uname)
        self.setGroup(filename, gname)
        self.setExtended(filename, stat)
        self.setModificationTime(filename, stat.st_mtime)
        self.setCreationTime(filename, stat.st_ctime)

    def __valid(self, fname, excludes):
        for ex in excludes:
            if ex.match(fname):
                return False

        return True

    def build(self, path, excludes=[]):
        if len(self._data) > 0:
            # this can be only done on empty list
            return None

        # compiling regex for exclusion
        __excludes = []
        for ex in excludes:
            __excludes.append(re.compile(ex))

        for dirpath, dirs, files in os.walk(path, followlinks=True):
            for dirname in dirs:
                fname = os.path.join(dirpath, dirname)

                # exclusion checking
                if not self.__valid(fname, __excludes):
                    continue

                if j.sal.fs.isEmptyDir(fname):
                    self._build(fname)

            for filename in files:
                fname = os.path.join(dirpath, filename)

                # exclusion checking
                if not self.__valid(fname, __excludes):
                    continue

                self._build(fname)

        return len(self._data)

    """
    Exporting
    """

    def dumps(self, trim=''):
        data = []

        for f in self._data:
            p = f[0]
            if p.startswith(trim):
                p = p[len(trim):]

            line = "%s|%s|%d|%s|%s|%s|%d|%d|%d|%s" % (
                p, f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9]
            )
            data.append(line)

        return "\n".join(data) + "\n"

    def _debug(self):
        tableMain = sys.getsizeof(self._data)
        tableHash = sys.getsizeof(self._hash)
        tablePath = sys.getsizeof(self._path)

        print("Main table: %.2f ko" % (float(tableMain) / 1024))
        print("Hash table: %.2f ko" % (float(tableHash) / 1024))
        print("Path table: %.2f ko" % (float(tablePath) / 1024))


class FListArchiver:
    # This is a not efficient way, the only other possibility
    # is to call brotli binary to compress big file if needed
    # currently, this in-memory way is used

    def __init__(self, ipfs_cfgdir=None):
        cl = j.tools.cuisine.local
        self._ipfs = cl.core.command_location('ipfs')
        if not ipfs_cfgdir:
            self._env = 'IPFS_PATH=%s' % cl.core.args_replace('$cfgDir/ipfs/main')
        else:
            self._env = 'IPFS_PATH=%s' % ipfs_cfgdir

    def _compress(self, source, destination):
        with open(source, 'rb') as content_file:
            content = content_file.read()

        compressed = brotli.compress(content, quality=6)

        with open(destination, "wb") as output:
            output.write(compressed)

    def push_to_ipfs(self, source):
        cmd = "%s %s add '%s'" % (self._env, self._ipfs, source)
        out = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)

        m = re.match(r'^added (.+) (.+)$', out.stdout.decode())
        if m is None:
            raise RuntimeError('invalid output from ipfs add: %s' % out)

        return m.group(1)

    def build(self, flist, backend):
        hashes = flist.getHashList()

        if not os.path.exists(backend):
            os.makedirs(backend)

        for hash in hashes:
            files = flist.filesFromHash(hash)

            # skipping non regular files
            if not flist.isRegular(files[0]):
                continue

            print("Processing: %s" % hash)

            root = "%s/%s/%s" % (backend, hash[0:2], hash[2:4])
            file = hash

            target = "%s/%s" % (root, file)

            if not os.path.exists(root):
                os.makedirs(root)

            # compressing the file
            self._compress(files[0], target)

            # adding it to ipfs network
            hash = self.push_to_ipfs(target)
            print("Network hash: %s" % hash)

            # updating flist hash with ipfs hash
            for f in files:
                flist.setHash(f, hash)

        print("Files compressed and shared")
