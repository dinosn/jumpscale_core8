import json


class Container:
    """G8SO Container"""

    def __init__(self, name, node, flist, hostname=None, filesystems=None, nics=None,
                 host_network=False, ports=None, storage=None, init_processes=None):
        """
        TODO: write doc string
        filesystems: dict {filesystemObj: target}
        """
        self.name = name
        self.node = node
        self.filesystems = filesystems or {}
        self.hostname = hostname
        self.flist = flist
        self.ports = ports or {}
        self.nics = nics or []
        self.host_network = host_network
        self.storage = storage
        self.init_processes = init_processes or []
        self._client = None

        self._ays = None

    @classmethod
    def from_ays(cls, service):
        from JumpScale.sal.g8os.Node import Node
        node = Node.from_ays(service.parent)
        ports = {}
        for portmap in service.model.data.ports:
            source, dest = portmap.split(':')
            ports[int(source)] = int(dest)
        nics = [nic.to_dict() for nic in service.model.data.nics]

        filesystems = {}
        for mount in service.model.data.mounts:
            fs_service = service.aysrepo.serviceGet('filesystem', mount.filesystem)
            try:
                sp = node.storagepools.get(fs_service.parent.name)
                fs = sp.get(fs_service.name)
            except KeyError:
                continue
            filesystems[fs] = mount.target

        container = cls(
            name=service.name,
            node=node,
            filesystems=filesystems,
            nics=nics,
            hostname=service.model.data.hostname,
            flist=service.model.data.flist,
            ports=ports,
            host_network=service.model.data.hostNetworking,
            storage=service.model.data.storage,
            init_processes=[p.to_dict() for p in service.model.data.initProcesses],
        )
        return container

    @property
    def id(self):
        for containerid, container in self.node.client.container.list().items():
            if self.name in container['container']['arguments']['tags'] or []:
                return int(containerid)
        return

    @property
    def client(self):
        if self._client is None:
            self._client = self.node.client.container.client(self.id)
        return self._client

    def _create_container(self, timeout=60):
        mounts = {}
        for fs, target in self.filesystems.items():
            mounts[fs.path] = target

        job = self.node.client.container.create(
            root_url=self.flist,
            mount=mounts,
            host_network=self.host_network,
            nics=self.nics,
            port=self.ports,
            tags=[self.name],
            hostname=self.hostname,
            storage=self.storage,
        )

        result = job.get(timeout)
        if result.state != 'SUCCESS':
            raise RuntimeError('failed to create container %s' % result.data)
        containerid = json.loads(result.data)
        self._client = self.node.client.container.client(containerid)

    def start(self):
        if not self.is_running():
            self._create_container()

            for process in self.init_processes:
                cmd = "{} {}".format(process['name'], ' '.join(process.get('args', [])))
                pwd = process.get('pwd', '')
                stdin = process.get('stdin', '')
                env = {}
                for x in process.get('environment', []):
                    k, v = x.split("=")
                    env[k] = v
                self.client.system(command=cmd, dir=pwd, stdin=stdin, env=env)

    def stop(self):
        if not self.is_running():
            return

        self.node.client.container.terminate(self.id)
        self._client = None

    def is_running(self):
        return self.id is not None

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale.sal.g8os.atyourservice.StorageCluster import ContainerAYS
            self._ays = ContainerAYS(self)
        return self._ays
