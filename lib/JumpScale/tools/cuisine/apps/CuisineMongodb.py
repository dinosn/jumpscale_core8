from JumpScale import j
from time import sleep


app = j.tools.cuisine._getBaseAppClass()


class CuisineMongodb(app):
    NAME = 'mongod'

    def install(self, start=True, reset=False):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        if (not reset and self.doneGet("install")) or self.isInstalled():
             return
        if self.cuisine.core.isMac:
            self.cuisine.core.run("brew uninstall mongodb", die=False)

        appbase = "%s/" % self.cuisine.core.dir_paths["BINDIR"]
        self.cuisine.core.dir_ensure(appbase)

        url = None
        if self.cuisine.core.isUbuntu:
            url = 'https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1604-3.4.0.tgz'
            dest = "$TMPDIR/mongodb-linux-x86_64-ubuntu1604-3.4.0/bin/"
        elif self.cuisine.core.isArch:
            self.cuisine.package.install("mongodb")
        elif self.cuisine.core.isMac:
            url = 'https://fastdl.mongodb.org/osx/mongodb-osx-ssl-x86_64-3.4.0.tgz'
            dest = "$TMPDIR/mongodb-osx-x86_64-3.4.0/bin/"
        else:
            raise j.exceptions.RuntimeError("unsupported platform")

        if url:
            self.logger.info('Downloading mongodb.')
            self.cuisine.core.file_download(url, to="$TMPDIR", overwrite=False, expand=True, timeout=0)
            tarpaths = self.cuisine.core.find("$TMPDIR", recursive=False, pattern="*mongodb*.tgz", type='f')
            if len(tarpaths) == 0:
                raise j.exceptions.Input(message="could not download:%s, did not find in %s" % (
                    url, self.replace("$TMPDIR")), level=1, source="", tags="", msgpub="")
            tarpath = tarpaths[0]
            self.cuisine.core.file_expand(tarpath, "$TMPDIR")

            for file in self.cuisine.core.find(dest, type='f'):
                self.cuisine.core.file_copy(file, appbase)

        self.cuisine.core.dir_ensure('$VARDIR/data/mongodb')
        self.doneSet("install")
        if start:
            self.start(reset=reset)

    def build(self, start=True, reset=False):
        raise RuntimeError("not implemented")

    def start(self, reset=False):
        if self.isStarted() and not reset:
            return
        self.cuisine.core.dir_ensure('$VARDIR/data/mongodb')
        cmd = "$BINDIR/mongod --dbpath '$VARDIR/data/mongodb'"
        self.cuisine.process.kill("mongod")
        self.cuisine.processmanager.ensure(name="mongod", cmd=cmd, env={}, path="", autostart=True)

    def stop(self):
        self.cuisine.processmanager.stop("mongod")
