from JumpScale import j

from ExecutorSSH import *
from ExecutorLocal import *


class ExecutorFactory:

    def __init__(self):
        self.__jslocation__ = "j.tools.executor"
        self._executors = {}

    def pushkey(self, addr, passwd, keyname="", pubkey="", port=22, login="root"):
        """
        @param keyname is name of key (pub)
        @param pubkey is the content of the pub key
        """
        ExecutorSSH(addr, port=port, login=login, passwd=passwd, pushkey=keyname, pubkey=pubkey)

    def get(self, executor="localhost"):
        """
        @param executor is an executor object, None or $hostname:$port or $ipaddr:$port or $hostname or $ipaddr
        """
        #  test if it's in cache
        if executor in self._executors:
            return self._executors[executor]

        if executor in ["localhost", "", None, "127.0.0.1"]:
            if 'localhost' not in self._executors:
                local = self.getLocal()
                self._executors['localhost'] = local
            return self._executors['localhost']

        elif j.data.types.string.check(executor):
            if executor.find(":") > 0:
                nbr = executor.count(':')
                login = 'root'
                if nbr == 1:
                    # ssh with port
                    addr, port = executor.split(":")
                if nbr == 2:
                    addr, port, login = executor.split(":")
                return self.getSSHBased(addr=addr.strip(), port=int(port), login=login)
            else:
                return self.getSSHBased(addr=executor.strip())
        else:
            return executor

    def getLocal(self, jumpscale=False, debug=False, checkok=False):
        return ExecutorLocal(debug=debug, checkok=debug)

    def getSSHBased(self, addr="localhost", port=22, login="root", passwd=None, debug=False, allow_agent=True, \
        look_for_keys=True, pushkey=None, pubkey="", timeout=5,usecache=True):
        key = '%s:%s:%s' % (addr, port, login)
        if key not in self._executors or usecache==False:
            print("ssh no cache")
            self._executors[key] = ExecutorSSH(addr=addr,
                                               port=port,
                                               login=login,
                                               passwd=passwd,
                                               debug=debug,
                                               allow_agent=allow_agent,
                                               look_for_keys=look_for_keys,
                                               pushkey=pushkey,
                                               pubkey=pubkey,
                                               timeout=timeout)
        return self._executors[key]

    def getSSHViaProxy(self, host):
        executor = ExecutorSSH()
        executor.getSSHViaProxy(host)
        self._executors[host] = executor
        return executor

    def getJSAgentBased(self, agentControllerClientKey, debug=False, checkok=False):
        return ExecutorAgent2(addr, debug=debug, checkok=debug)

    def reset(self, executor):
        """
        reset remove the executor passed in argument from the cache.
        """
        if j.data.types.string.check(executor):
            key = executor
        elif executor.type == 'ssh':
            key = '%s:%s:%s' % (executor.addr, executor.port, executor.login)
        else:
            raise j.exceptions.Input(message='executor type not recognize.')
        if key in self._executors:
            exe = self._executors[key]
            j.tools.cuisine.reset(exe.cuisine)
            del self._executors[key]
