import os
from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineRedis(app):
    NAME = 'redis-server'

    def reset(self):
        app.reset(self)
        self._init()

    def build(self, reset=False, start=False):
        os.environ["LC_ALL"] = "C.UTF-8"
        os.environ["LANG"] = "C.UTF-8"

        """Building and installing redis"""
        if reset is False and self.isInstalled():
            self.logger.info('Redis is already installed, pass reset=True to reinstall.')
            return

        if self.cuisine.core.isUbuntu:
            self.cuisine.package.update()
            self.cuisine.package.install("build-essential")

            self.cuisine.core.dir_remove("$TMPDIR/build/redis")

            C = """
            #!/bin/bash
            set -ex

            # groupadd -r redis && useradd -r -g redis redis

            mkdir -p $TMPDIR/build/redis
            cd $TMPDIR/build/redis
            wget http://download.redis.io/redis-stable.tar.gz
            tar xzf redis-stable.tar.gz
            cd redis-stable
            make

            rm -f /usr/local/bin/redis-server
            rm -f /usr/local/bin/redis-cli
            """

            C = self.cuisine.bash.profileJS.replace(C)
            C = self.replace(C)
            self.cuisine.core.run(C)

            # move action
            C = """
            set -ex
            mkdir -p $BASEDIR/bin/
            cp -f $TMPDIR/build/redis/redis-stable/src/redis-server $BINDIR
            cp -f $TMPDIR/build/redis/redis-stable/src/redis-cli $BINDIR
            rm -rf $BASEDIR/apps/redis
            """
            C = self.cuisine.core.replace(C)
            C = self.replace(C)
            self.cuisine.core.run(C)
        else:
            raise j.exceptions.NotImplemented(
                message="only ubuntu supported for building redis", level=1, source="", tags="", msgpub="")

        if start is True:
            self.start()

    def isInstalled(self):
        return self.cuisine.core.command_check('redis-server') and self.cuisine.core.command_check('redis-cli')

    def install(self, reset=False):
        return self.build(reset=reset)

    def start(self, name="main", ip="localhost", port=6379, maxram="50mb", appendonly=True,
              snapshot=False, slave=(), ismaster=False, passwd=None, unixsocket=None):

        redis_cli = j.sal.redis.getInstance(self.cuisine)
        if unixsocket is not None:
            redisSocket = j.sal.fs.getParent(unixsocket)
            self.cuisine.core.dir_ensure(redisSocket)
        redis_cli.configureInstance(name,
                                    ip,
                                    port,
                                    maxram=maxram,
                                    appendonly=appendonly,
                                    snapshot=snapshot,
                                    slave=slave,
                                    ismaster=ismaster,
                                    passwd=passwd,
                                    unixsocket=unixsocket)
        # return if redis is already running
        if redis_cli.isRunning(ip_address=ip, port=port, path='$BINDIR', password=passwd, unixsocket=unixsocket):
            self.logger.info('Redis is already running!')
            return

        _, cpath = j.sal.redis._getPaths(name)

        cmd = "$BINDIR/redis-server %s" % cpath
        self.cuisine.processmanager.ensure(name="redis_%s" % name, cmd=cmd, env={}, path='$BINDIR', autostart=True)

        # Checking if redis is started correctly with port specified
        if not redis_cli.isRunning(ip_address=ip, port=port, path='$BINDIR', unixsocket=unixsocket):
            raise j.exceptions.RuntimeError('Redis is failed to start correctly')

    def stop(self, name='main'):
        self.cuisine.processmanager.stop(name="redis_%s" % name)
