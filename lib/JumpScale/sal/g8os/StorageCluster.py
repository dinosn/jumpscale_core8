from JumpScale import j
from JumpScale.sal.g8os.Disk import DiskType
from JumpScale.sal.g8os.Container import Container
from JumpScale.sal.g8os.ARDB import ARDB


class StorageCluster:
    """StorageCluster is a cluster of ardb servers"""

    def __init__(self, label):
        """
        @param label: string repsenting the name of the storage cluster
        """
        self.label = label
        self.name = label
        self.nodes = []
        self.filesystems = []
        self.storage_servers = []
        self.disk_type = None
        self.has_slave = None
        self._ays = None

    @classmethod
    def from_ays(cls, service):
        j.sal.g8os.logger.debug("load cluster storage cluster from service (%s)", service)
        cluster = cls(label=service.name)
        cluster.disk_type = str(service.model.data.diskType)
        cluster.has_slave = service.model.data.hasSlave

        for ardb_service in service.producers.get('ardb', []):
            storages_server = StorageServer.from_ays(ardb_service)
            cluster.storage_servers.append(storages_server)
            if storages_server.node not in cluster.nodes:
                cluster.nodes.append(storages_server.node)

        return cluster

    def get_config(self):
        data = {'dataStorage': [],
                'metadataStorage': None,
                'label': self.name,
                'status': 'ready' if self.is_running() else 'error',
                'nodes': [node.name for node in self.nodes]}
        for storageserver in self.storage_servers:
            if storageserver.master:
                # config file does not care about slaves
                continue
            if 'metadata' in storageserver.name:
                data['metadataStorage'] = storageserver.ardb.bind
            else:
                data['dataStorage'].append(storageserver.ardb.bind)
        return data

    @property
    def nr_server(self):
        """
        Number of storage server part of this cluster
        """
        return len(self.storage_servers)

    def create(self, nodes, disk_type, nr_server, has_slave=True):
        """
        @param nodes: list of node on wich we can deploy storage server
        @param disk_type: type of disk to be used by the storage server
        @param nr_server: number of storage server to deploy
        @param has_slave: boolean specifying of we need to deploy slave storage server
        """
        j.sal.g8os.logger.debug("start creation of cluster %s", self.label)
        self.nodes = nodes
        if disk_type not in DiskType.__members__.keys():
            raise TypeError("disk_type should be on of {}".format(', '.join(DiskType.__members__.keys())))
        self.disk_type = disk_type
        self.has_slave = has_slave
        if len(nodes) < 2 and has_slave:
            raise RuntimeError("can't deploy storage cluster with slaves if deployed on less then two nodes")


        for disk in self._find_available_disks():
            self.filesystems.append(self._prepare_disk(disk))

        nr_filesystems = len(self.filesystems)

        def get_filesystem(i, exclude_node=None):
            fs = self.filesystems[i % (nr_filesystems - 1)]
            while exclude_node is not None and fs.pool.node == exclude_node:
                i += 1
                fs = self.filesystems[i % (nr_filesystems - 1)]
            return fs

        # deploy data storage server
        port = 2000
        for i in range(nr_server):
            fs = get_filesystem(i)
            bind = "{}:{}".format(fs.pool.node.storageAddr, port)
            port = port + 1
            storage_server = StorageServer(cluster=self)
            storage_server.create(filesystem=fs, name="{}_data_{}".format(self.name, i), bind=bind)
            self.storage_servers.append(storage_server)

        if has_slave:
            for i in range(nr_server):
                storage_server = self.storage_servers[i]
                fs = get_filesystem(i, storage_server.node)
                bind = "{}:{}".format(fs.pool.node.storageAddr, port)
                port = port + 1
                slave_server = StorageServer(cluster=self)
                slave_server.create(filesystem=fs, name="{}_data_{}".format(self.name, (nr_server + i)), bind=bind, master=storage_server)
                self.storage_servers.append(slave_server)

        # deploy metadata storage server
        fs = get_filesystem(0)
        bind = "{}:{}".format(fs.pool.node.storageAddr, port)
        port = port + 1
        metadata_storage_server = StorageServer(cluster=self)
        metadata_storage_server.create(filesystem=fs, name="{}_metadata_0".format(self.name), bind=bind)
        self.storage_servers.append(metadata_storage_server)

        if has_slave:
            fs = get_filesystem(i, metadata_storage_server.node)
            bind = "{}:{}".format(fs.pool.node.storageAddr, port)
            port = port + 1
            slave_server = StorageServer(cluster=self)
            slave_server.create(filesystem=fs, name="{}_metadata_1".format(self.name), bind=bind, master=metadata_storage_server)
            self.storage_servers.append(slave_server)

    def _find_available_disks(self):
        """
        return a list of disk that are not used by storage pool
        or has a different type as the one required for this cluster
        """
        j.sal.g8os.logger.debug("find available_disks")
        cluster_name = 'sp_cluster_{}'.format(self.label)
        available_disks = []

        def check_partition(disk):
            for partition in disk.partitions:
                for filesystem in partition.filesystems:
                    if filesystem['label'].startswith(cluster_name):
                        return True

        for node in self.nodes:
            for disk in node.disks.list():
                # skip disks of wrong type
                if disk.type.name != self.disk_type:
                    continue
                # skip devices which have filesystems on the device
                if len(disk.filesystems) > 0:
                    continue

                # skip devices which have partitions
                if len(disk.partitions) == 0:
                    available_disks.append(disk)
                else:
                    if check_partition(disk):
                        available_disks.append(disk)

        return available_disks

    def _prepare_disk(self, disk):
        """
        _prepare_disk make sure a storage pool and filesytem are present on the disk.
        returns the filesytem created
        """
        name = "cluster_{}_{}".format(self.label, disk.name)
        j.sal.g8os.logger.debug("prepare disk %s", disk.devicename)
        try:
            pool = disk.node.storagepools.get(name)
        except ValueError:
            pool = disk.node.storagepools.create(name, [disk.devicename], 'single', 'single', overwrite=True)

        pool.mount()
        try:
            fs = pool.get(name)
        except ValueError:
            fs = pool.create(name)

        return fs

    def start(self):
        j.sal.g8os.logger.debug("start %s", self)
        for server in self.storage_servers:
            server.start()

    def stop(self):
        j.sal.g8os.logger.debug("stop %s", self)
        for server in self.storage_servers:
            server.stop()

    def is_running(self):
        # TODO: Improve this, what about part of server running and part stopped
        for server in self.storage_servers:
            if not server.is_running():
                return False
        return True

    def health(self):
        """
        Return a view of the state all storage server running in this cluster
        example :
        {
        'cluster1_1': {'ardb': True, 'container': True, 'slaveof': None},
        'cluster1_2': {'ardb': True, 'container': True, 'slaveof': None},
        }
        """
        health = {}
        for server in self.storage_servers:
            running, _ = server.ardb.is_running()
            health[server.name] = {
                'ardb': running,
                'container': server.container.is_running(),
                'slaveof': server.master.name if server.master else None,
            }
        return health

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale.sal.g8os.atyourservice.StorageCluster import StorageClusterAys
            self._ays = StorageClusterAys(self)
        return self._ays

    def __repr__(self):
        return "StorageCluster <{}>".format(self.label)


class StorageServer:
    """ardb servers"""

    def __init__(self, cluster):
        self.cluster = cluster
        self.container = None
        self.ardb = None
        self.master = None

    def create(self, filesystem, name, bind='0.0.0.0:16739', master=None):
        j.sal.g8os.logger.debug("create storage server %s in cluster %s", name, self.cluster.label)
        self.master = master
        self.container = Container(
            name=name,
            node=filesystem.pool.node,
            flist="https://hub.gig.tech/gig-official-apps/ardb-rocksdb.flist",
            mounts={filesystem.path: '/mnt/data'},
            host_network=True,
        )
        self.ardb = ARDB(
            name=name,
            container=self.container,
            bind=bind,
            data_dir='/mnt/data/{}'.format(name),
            master=master.ardb if master else None
        )

    @classmethod
    def from_ays(cls, ardb_services):
        ardb = ARDB.from_ays(ardb_services)
        container = Container.from_ays(ardb_services.parent)
        storage_server = cls(None)
        storage_server.container = container
        storage_server.ardb = ardb
        if ardb.master:
            storage_server.master = cls(None)
            storage_server.master.container = ardb.master.container
            storage_server.master.ardb = ardb.master
        return storage_server

    @property
    def name(self):
        if self.ardb:
            return self.ardb.name
        return None

    @property
    def node(self):
        if self.container:
            return self.container.node
        return None

    def _find_port(self, start_port=2000):
        while True:
            if j.sal.nettools.tcpPortConnectionTest(self.node.addr, start_port, timeout=2):
                start_port += 1
                continue
            return start_port

    def start(self, timeout=30):
        j.sal.g8os.logger.debug("start %s", self)
        if self.master:
            self.master.start()

        if not self.container.is_running():
            self.container.start()

        ip, port = self.ardb.bind.split(":")
        self.ardb.bind = '{}:{}'.format(ip, self._find_port(port))
        self.ardb.start(timeout=timeout)

    def stop(self, timeout=30):
        j.sal.g8os.logger.debug("stop %s", self)
        self.ardb.stop(timeout=timeout)
        self.container.stop()

    def is_running(self):
        container = self.container.is_running()
        ardb, _ = self.ardb.is_running()
        return (container and ardb)
