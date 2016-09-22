from JumpScale import j

import os
import sys
import time
import traceback
import fcntl
import copy
# don't do logging, slows down

import multiprocessing


class Process():

    def __init__(self, name="", method=None, args={}):
        self.name = name
        self.method = method
        self.args = args

        self.value = None
        self.error = None
        self.stdout = ""
        self.stderr = ""
        self.outpipe = None
        self.state = "init"

        self.new_stdout = ""
        self.new_stderr = ""

        self._stdout = {'read': None, 'write': None, 'fd': None}
        self._stderr = {'read': None, 'write': None, 'fd': None}

    def _flush(self):
        sys.stdout.flush()
        sys.stderr.flush() # should be not necessary, stderr is unbuffered by default

    def _close(self):
        sys.stdout.close()
        sys.stderr.close()

    def _clean(self):
        self._flush()
        self._close()

    def _setResult(self, value):
        self.outpipe.write(j.data.serializer.json.dumps(value) + "\n")
        self.outpipe.flush()

    def _setSuccess(self, retval):
        self._state = "success"
        self._setResult({"status": self._state, "return": retval})

    def _setPanic(self):
        self._state = "panic"
        self._setResult({"status": self._state, "return": -1})

    def _setException(self, exception):
        self._state = "exception"
        self._setResult({"status": self._state, "return": -1, "eco": exception})

    def start(self):
        if self.method == None:
            msg = "Cannot start process, method not set."
            raise j.exceptions.Input(message=msg, level=1, source="", tags="", msgpub="")

        rpipe, wpipe = os.pipe()
        self._stdout['read'], self._stdout['write'] = os.pipe()
        self._stderr['read'], self._stderr['write'] = os.pipe()

        pid = os.fork()
        if pid == -1:
            raise RuntimeError("Failed to fork()")

        res = None

        if pid == 0:
            # Child -- do the copy, print log to pipe and exit
            try:
                os.close(rpipe)
                os.dup2(self._stdout['write'], sys.stdout.fileno())
                os.dup2(self._stderr['write'], sys.stderr.fileno())
                self.outpipe = os.fdopen(wpipe, 'w')

                # print("ARGS:%s" % args)
                # j.core.processmanager.clearCaches()
                self._state = "running"
                res = self.method(**self.args)

            except Exception as e:
                eco = j.errorconditionhandler.processPythonExceptionObject(e)

                self._setException(eco.toJson())
                self._clean()
                os._exit(1)

            finally:
                self._setSuccess(res)
                self._clean()
                os._exit(0)

            # should never arrive here
            self._setPanic()
            os._exit(1)

        else:
            os.close(wpipe)
            os.close(self._stdout['write'])
            os.close(self._stderr['write'])
            self.pid = pid

            # setting pipes in non-block, to catch "running" later
            self.outpipe = os.fdopen(rpipe)
            fcntl.fcntl(self.outpipe, fcntl.F_SETFL, os.O_NONBLOCK)

            self._stdout['fd'] = os.fdopen(self._stdout['read'])
            fcntl.fcntl(self._stdout['fd'], fcntl.F_SETFL, os.O_NONBLOCK)

            self._stderr['fd'] = os.fdopen(self._stderr['read'])
            fcntl.fcntl(self._stderr['fd'], fcntl.F_SETFL, os.O_NONBLOCK)

    def _readAvailable(self, fd):
        temp = ""
        for block in iter(lambda: fd.read(8), ""):
            temp += block

        return temp

    def isDone(self):
        return (self.state != "running" and self.state != "init")

    def sync(self):
        if self.pid == None:
            return self.state

        # nothing to do more if the process is done
        if self.isDone():
            return self.state

        temp = self._readAvailable(self.outpipe)
        self._syncStd()

        # if the pipe is empty, the process is still running
        if temp == "":
            data = {"status": "running"}

        # otherwise, process is ended and we know the result
        else:
            data = j.data.serializer.json.loads(temp)

        # update local class with data
        self._update(data)

        return data['status']

    def _syncStd(self):
        self.new_stdout = self._readAvailable(self._stdout['fd'])
        self.new_stderr = self._readAvailable(self._stderr['fd'])

        self.stdout += self.new_stdout
        self.stderr += self.new_stderr

    def _update(self, data):
        self.state = data['status']

        if data['status'] == 'running':
            return

        self.value = data['return']

        if data['status'] == 'exception':
            self.error = data['eco']


    def wait(self):
        # wait until a process the process is finished
        if self.pid == None:
            return

        try:
            data = os.waitpid(self.pid, 0)
            if self.sync() != "running":
                self.pid = None

        except Exception as e:
            # print("waitpid: ", e)
            pass

    def __repr__(self):
        out = "Process name: %s, status: %s, return: %s" % (self.name, self.state, self.value)

        if self.state != "running":
            out += "\n== Stdout ==\n%s" % self.stdout
            out += "\n== Stderr ==\n%s" % self.stderr

        if self.state == "exception":
            out += "\nError:\n%s" % self.error

        return out

    def close(self):
        self.sync()
        self.outpipe.close()

        # clear child if process is done
        if self.isDone():
            self.wait()

        # kill child if still running
        if self.state == "running":
            j.sal.process.kill(self.pid)
            self._syncStd()
            self.wait()
            self.state = "killed"

        self.pid = None

    __str__ = __repr__


class ProcessManagerFactory:

    def __init__(self):
        self.__jslocation__ = "j.core.processmanager"
        self._lastnr = 0
        self.processes = {}

    def clearCaches(self):
        """
        call this in subprocess if you want to make sure that no sockets will be reused
        """
        j.clients.ssh.cache = {}
        j.clients.redis._redis = {}
        j.clients.redis._redisq = {}
        j.clients.postgres.clients = {}

        # j.core.db = Redis(unix_socket_path='/tmp/redis.sock')

    def getQueue(self, size=1000):
        """
        can get this & give to startProcess in args (see test)
        """
        return multiprocessing.Queue(size)

    def getProcess(self, method=None, args={}, name="", autoclear=True, autowait=True):
        if name == "":
            name = "process_%s" % self._lastnr
            self._lastnr += 1

        if len(self.processes) > 100 and autoclear:
            self.clear()

        if len(self.processes) > 100:
            print("no clear")

            if autowait:
                if autoclear == False:
                    raise j.exceptions.Input(message="cannot wait if autoclear=False",
                                             level=1, source="", tags="", msgpub="")
                while True:
                    print("too many subprocesses, am waiting")
                    time.sleep(1)
                    self.clear()
                    time.sleep(1)
                    if len(self.processes) < 100:
                        break
            else:
                raise j.exceptions.Input(message="cannot launch more than 100 sub processes",
                                         level=1, source="", tags="", msgpub="")

        p = Process(name, method, args)
        self.processes[p.name] = p
        return p

    def startProcess(self, method, args={}, name="", autoclear=True, autowait=True):
        p = self.getProcess(method=method, args=args, name=name, autoclear=autoclear, autowait=autowait)
        p.start()
        return p

    def clear(self, error=False):
        # print("clearing process list")
        keys = [item for item in self.processes.keys()]
        cleared = 0

        # print(len(keys))
        for key in keys:
            p = self.processes[key]
            status = p.sync()

            if (status == "error" and error) or status == "success":
                p.close()
                self.processes.pop(p.name)
                cleared += 1

        return cleared



    def test(self):
        """
        Simple test, spaw, processes and wait for them
        """
        def amethod(x=None, till=1):
            counter = 0
            print("OK:%s" % x)
            while True:
                counter += 1
                sys.stderr.write("Counter: %d\n" % counter)
                time.sleep(0.1)

                if counter == till:
                    return x

        r = {}
        nr = 10

        print(" * Testing simple method x%d" % nr)

        for i in range(nr):
            r[i] = self.startProcess(amethod, {"x": i, "till": 1})

        for i in range(nr):
            r[i].wait()
            print(r[i])

        print(" * Simple method done.")

        """
        Simple error managemebt.
        """
        print(" * Testing error")

        def anerror(x=None, till=1):
            print("a line - normal")
            print("a line2 - normal")
            j.logger.log("testlog")
            raise RuntimeError("raised, generic python error")

        p = self.startProcess(anerror, {"x": i, "till": 1})
        p.wait()

        # next should print the error & the log
        print(p)

        print(" * Error done.")

        """
        Test a process which waits for data from a queue and stop on specific value
        """
        print(" * Testing queue")

        def queuetest(queue):
            counter = 0
            print("Queue Inner test")
            while True:
                if not queue.empty():
                    last = queue.get()
                    counter += 1
                    print("From queue: %s" % last)
                    if last == "stop":
                        return last

                    time.sleep(0.1)

                else:
                    return "empty"

        q = self.getQueue()
        q.put("test1")
        q.put("test2")
        q.put("test3")
        q.put("test4")
        q.put("test5")
        q.put("stop")   # remove me to test the queue²

        p = self.startProcess(queuetest, {"queue": q})

        # fill the queue here

        p.wait()
        print(p)

        print(" * Queue done.")

        """
        Simple slow process, and fetch asynchronously stdout and stderr
        """

        print(" * Testing slow process")

        def slowprocess(till):
            print("Init slow process")
            x = 0
            while x < till:
                print("Waiting %d" % x)
                time.sleep(1)
                x += 1

            return 0

        p = self.startProcess(slowprocess, {'till': 10})
        while p.sync() == "running":
            if p.new_stdout:
                print("stdout >> %s" % p.new_stdout)

            if p.new_stderr:
                print("stderr >> %s" % p.new_stderr)

            time.sleep(2)

        p.wait()
        print(p)

        print(" * Slow process done.")

        """
        Spawn a process and kill it before it ends
        """
        print(" * Testing prematured close")

        def prematured(timewait):
            print("Waiting %.2f seconds" % timewait)
            time.sleep(timewait)
            print("Timewait elapsed")
            return 0

        p = self.startProcess(prematured, {'timewait': 5})
        time.sleep(1)
        p.close()
        print(p)

        print(" * Prematured test done.")

    def perftest(self):

        # can run more than 1000 process per sec

        def amethod(x=None, till=1):
            print("I'm process %d" % x)
            return x

        r = {}
        nr = 1500
        start = time.time()
        print("Starting benchmark, launching %d processes" % nr)

        for i in range(nr):
            r[i] = self.startProcess(amethod, {"x": i, "till": 1})

        for i in range(nr):
            r[i].wait()

        print(r[100])
        cl = self.clear()
        print("Process cleared at the end: %d" % cl)

        diff = time.time() - start
        pps = int(nr / diff)

        print("Number of processes per seconds: %s (%d process in %d seconds)" % (pps, nr, diff))
