import io
import time
from JumpScale import j



class ARDB:
    """ardb server"""

    def __init__(self, name, container, bind='0.0.0.0:16379', data_dir='/mnt/data', master=None):
        """
        TODO: write doc string
        """
        self.name = name
        self.master = master
        self.container = container
        self.bind = bind
        self.data_dir = data_dir
        self.master = master
        self._ays = None

    @classmethod
    def from_ays(cls, service):
        j.sal.g8os.logger.debug("create ardb from service (%s)", service)
        from JumpScale.sal.g8os.Container import Container

        container = Container.from_ays(service.parent)
        if service.model.data.master != '':
            master_service = service.aysrepo.serviceGet('ardb', service.model.data.master)
            master = ARDB.from_ays(master_service)
        else:
            master = None

        return cls(
            name=service.name,
            container=container,
            bind=service.model.data.bind,
            data_dir=service.model.data.homeDir,
            master=master,
        )

    def _configure(self):
        j.sal.g8os.logger.debug("configure ardb")
        buff = io.BytesIO()
        self.container.client.filesystem.download('/etc/ardb.conf', buff)
        content = buff.getvalue().decode()

        # update config
        content = content.replace('/mnt/data', self.data_dir)
        content = content.replace('0.0.0.0:16379', self.bind)

        if self.master is not None:
            _, port = self.master.bind.split(":")
            content = content.replace('#slaveof 127.0.0.1:6379', 'slaveof {}:{}'.format(self.master.container.node.addr, port))

        # make sure home directory exists
        self.container.client.filesystem.mkdir(self.data_dir)

        # upload new config
        self.container.client.filesystem.upload('/etc/ardb.conf.used', io.BytesIO(initial_bytes=content.encode()))

    def start(self, timeout=30):
        if not self.container.is_running():
            self.container.start()

        running, _ = self.is_running()
        if running:
            return
        j.sal.g8os.logger.debug('start %s', self)

        self._configure()

        self.container.client.system('/bin/ardb-server /etc/ardb.conf.used')

        # wait for ardb to start
        start = time.time()
        end = start + timeout
        is_running, _ = self.is_running()
        while not is_running and time.time() < end:
            time.sleep(1)
            is_running, _ = self.is_running()

        if not is_running:
            raise RuntimeError("storage server {} didn't started".format(self.name))

    def stop(self, timeout=30):
        if not self.container.is_running():
            return

        is_running, job = self.is_running()
        if not is_running:
            return

        j.sal.g8os.logger.debug('stop %s', self)

        self.container.client.job.kill(job['cmd']['id'])

        # wait for ardb to stop
        start = time.time()
        end = start + timeout
        is_running, _ = self.is_running()
        while is_running and time.time() < end:
            time.sleep(1)
            is_running, _ = self.is_running()

        if is_running:
            raise RuntimeError("storage server {} didn't stopped")

    def is_running(self):
        try:
            for job in self.container.client.job.list():
                if 'name' in job['cmd']['arguments'] and job['cmd']['arguments']['name'] == '/bin/ardb-server':
                    return (True, job)
            return (False, None)
        except Exception as err:
            if str(err).find("invalid container id"):
                return (False, None)
            raise

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale.sal.g8os.atyourservice.StorageCluster import ARDBAys
            self._ays = ARDBAys(self)
        return self._ays

    def __str__(self):
        return "ARDB <{}>".format(self.name)

    def __repr__(self):
        return str(self)
