

import sys
import os
import time
import re

if sys.platform.startswith('linux') or sys.platform.startswith('sunos'):
    import fcntl

from JumpScale import j

# THIS METHOD IS NOT THREADSAFE

#TODO Fixup singleton-like behavior
class Lock:

    _LOCKPATHLINUX = "/tmp/run"
    __LOCKDICTIONARY = {}

    __shared_state = {}

    def __init__(self):
        self.__jslocation__ = "j.tools.lock"
        self.__dict__ = self.__shared_state
        self._LOCKPATHWIN = os.getcwd()+os.sep+'tmp'+os.sep+'run'+os.sep

    def lock(self, lockname, locktimeout=60):
        """ Take a system-wide interprocess exclusive lock. Default timeout is 60 seconds """

        if locktimeout < 0:
            raise RuntimeError("Cannot take lock [%s] with negative timeout [%d]" % (lockname, locktimeout))

        if j.core.platformtype.isUnix():
            # linux implementation
            lockfile = self._LOCKPATHLINUX + os.sep + self.cleanupString(lockname)
            j.sal.fs.createDir(Util._LOCKPATHLINUX)
            j.sal.fs.createEmptyFile(lockfile)

            # Do the locking
            lockAcquired = False
            for i in range(locktimeout+1):
                try:
                    myfile = open(lockfile, "r+")
                    fcntl.flock(myfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lockAcquired = True
                    self.__LOCKDICTIONARY[lockname] = myfile
                    break
                except IOError:
                    # Did not get the lock :( Sleep 1 second and then retry
                    time.sleep(1)
            if not lockAcquired:
                myfile.close()
                raise RuntimeError("Cannot acquire lock [%s]" % (lockname))

        elif j.core.platformtype.isWindows():
            raise NotImplementedError

    def unlock(self, lockname):
        """ Unlock system-wide interprocess lock """
        if j.core.platformtype.isUnix():
            try:
                myfile = self.__LOCKDICTIONARY.pop(lockname)
                fcntl.flock(myfile.fileno(), fcntl.LOCK_UN)
                myfile.close()
            except Exception as exc:
                raise RuntimeError("Cannot unlock [%s] with ERROR:%s" % (lockname, str(exc)))

        elif j.core.platformtype.isWindows():
            raise NotImplementedError