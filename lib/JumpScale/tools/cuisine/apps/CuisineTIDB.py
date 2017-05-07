from JumpScale import j
from time import sleep


app = j.tools.cuisine._getBaseAppClass()


class CuisineTIDB(app):
    """
    Installs TIDB.
    """
    NAME = 'tidb-server'

    def _init(self):
        self.BUILDDIR = self.replace("$BUILDDIR/tidb/")

    def reset(self):
        app.reset(self)
        self._init()

    def build(self, install=True, reset=False):
        """
        Build requires both golang and rust to be available on the system
        """

        if self.doneGet('build') and reset is False:
            return

        self.cuisine.package.mdupdate()
        self.cuisine.package.install('build-essential')

        self.cuisine.core.dir_ensure(self.BUILDDIR)
        tidb_url = 'http://download.pingcap.org/tidb-latest-linux-amd64.tar.gz'
        dest = j.sal.fs.joinPaths("$BUILDDIR", 'tidb-latest-linux-amd64.tar.gz')
        # build_script = self.cuisine.core.file_download('https://raw.githubusercontent.com/pingcap/docs/master/scripts/build.sh', \
        #     j.sal.fs.joinPaths(self.BUILDDIR, 'build.sh'),minsizekb=0)
        #
        # self.cuisine.core.run('cd {builddir}; bash {build}'.format(builddir=self.BUILDDIR, build=build_script), profile=True, timeout=1000)
        if not self.cuisine.core.file_exists(dest):
            self.cuisine.core.file_download(tidb_url, dest, timeout=900)
        self.cuisine.core.run(
            'cd $BUILDDIR && tar xvf tidb-latest-linux-amd64.tar.gz && cp -r $BUILDDIR/tidb-latest-linux-amd64/* {builddir}'.format(builddir=self.BUILDDIR))
        self.doneSet('build')

        if install:
            self.install(False)

    def install(self, start=True):
        """
        install, move files to appropriate places, and create relavent configs
        """
        if self.doneGet('install'):
            return

        self.cuisine.core.run("cp $BUILDDIR/tidb/bin/* $BINDIR/")
        #for path in self.cuisine.core.find(j.sal.fs.joinPaths(self.BUILDDIR, 'bin'), type='f'):
        #    self.cuisine.core.file_copy(path, '$BINDIR')

        self.doneSet('install')

        if start:
            self.start()

    def start_pd_server(self, clusterId=1):
        config = {
            'clusterId': clusterId,
            'dataDir': j.sal.fs.joinPaths(j.dirs.VARDIR, 'tidb'),
        }
        self.cuisine.processmanager.ensure(
            'tipd',
            'pd-server --data-dir={dataDir}'.format(**config),
        )

    def start_tikv(self, clusterId=1):
        config = {
            'clusterId': clusterId,
            'dataDir': j.sal.fs.joinPaths(j.dirs.VARDIR, 'tidb'),
        }
        self.cuisine.processmanager.ensure(
            'tikv',
            'tikv-server --pd 127.0.0.1:2379 -s tikv1'.format(**config)
        )

    def start_tidb(self, clusterId=1):
        config = {
            'clusterId': clusterId,
            'dataDir': j.sal.fs.joinPaths(j.dirs.VARDIR, 'tidb'),
        }
        self.cuisine.processmanager.ensure(
            'tidb',
            'tidb-server -P 3306 --store=tikv \
            --path="127.0.0.1:2379"'.format(**config)
        )

    def start(self, clusterId=1):
        """
        Read docs here.
        https://github.com/pingcap/docs/blob/master/op-guide/clustering.md
        """
        # Start a standalone cluster
        self.start_pd_server()
        if not self._check_running('pd-server', timeout=30):
            raise j.exceptions.RuntimeError("tipd didn't start")

        self.start_tikv()
        if not self._check_running('tikv-server', timeout=30):
            raise j.exceptions.RuntimeError("tikv didn't start")

        self.start_tidb()
        if not self._check_running('tidb-server', timeout=30):
            raise j.exceptions.RuntimeError("tidb didn't start")

    def stop(self):
        self.cuisine.processmanager.stop("tidb-server")
        self.cuisine.processmanager.stop("pd-server")
        self.cuisine.processmanager.stop("tikv-server")

    def _check_running(self, name, timeout=30):
        """
        check that a process is running.
        name: str, name of the process to check
        timout: int, timeout in second
        """
        now = j.data.time.epoch
        cmd = "ps aux | grep {}".format(name)
        rc, _, _ = self.cuisine.core.run(cmd, die=False, showout=False)
        while rc != 0 and j.data.time.epoch < (now + timeout):
            rc, _, _ = self.cuisine.core.run(cmd, die=False, showout=False)
            if rc != 0:
                sleep(2)
        return rc == 0
