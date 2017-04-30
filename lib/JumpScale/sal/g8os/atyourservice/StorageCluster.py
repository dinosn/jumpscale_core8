from JumpScale import j
from JumpScale.sal.g8os.abstracts import AYSable


class StorageClusterAys(AYSable):

    def __init__(self, storagecluster):
        self._obj = storagecluster
        self.actor = 'storage_cluster'

    def create(self, aysrepo):
        # create all producers
        filesystems = []
        ardbs = []

        for fs in self._obj.filesystems:
            try:
                pool_service = fs.pool.ays.get(aysrepo)
            except ValueError:
                pool_service = fs.pool.ays.create(aysrepo)

            try:
                fs_service = fs.ays.get(aysrepo)
            except ValueError:
                fs_service = fs.ays.create(aysrepo)
            fs_service.consume(pool_service)
            filesystems.append(fs_service)

        for server in self._obj.storage_servers:
            try:
                container_service = server.container.ays.get(aysrepo)
            except ValueError:
                container_service = server.container.ays.create(aysrepo)

            try:
                ardb_services = server.ardb.ays.get(aysrepo)
            except ValueError:
                ardb_services = server.ardb.ays.create(aysrepo)
            ardb_services.consume(container_service)
            ardbs.append(ardb_services)

        actor = aysrepo.actorGet(self.actor)
        args = {
            'label': self._obj.name,
            # 'status':
            'nrServer': self._obj.nr_server,
            'hasSlave': self._obj.has_slave,
            'diskType': str(self._obj.disk_type),
            'nodes': [node.name for node in self._obj.nodes],
        }
        cluster_service = actor.serviceCreate(instance=self._obj.name, args=args)

        cluster_service.model.data.init('ardbs', len(ardbs))
        cluster_service.model.data.init('filesystems', len(filesystems))

        for index, service in enumerate(filesystems):
            cluster_service.consume(service)
            cluster_service.model.data.filesystems[index] = service.name

        for index, service in enumerate(ardbs):
            cluster_service.consume(service)
            cluster_service.model.data.ardbs[index] = service.name

        cluster_service.saveAll()
        return cluster_service


def clean_dict(d):
    for k in list(d.keys()):
        if d[k] is None:
            del d[k]
    return d


class ContainerAYS(AYSable):

    def __init__(self, storageserver):
        self._obj = storageserver
        self.actor = 'container'

    def get(self, aysrepo):
        """
        get the AYS service
        """
        try:
            service = aysrepo.serviceGet(role=self.role, instance=self.name)
            service.model.data.id = self._obj.id or 0
            return service
        except j.exceptions.NotFound:
            raise ValueError("Could not find {} with name {}".format(self.role, self.name))

    def create(self, aysrepo):
        actor = aysrepo.actorGet(self.actor)
        args = {
            'node': self._obj.node.name,
            'hostname': self._obj.hostname,
            'flist': self._obj.flist,
            # 'initProcesses': ,TODO
            # 'zerotier': ,
            # 'bridges': ,
            'hostNetworking': self._obj.host_network,
            'storage': self._obj.storage,
            'id': self._obj.id,
        }
        service = actor.serviceCreate(instance=self._obj.name, args=clean_dict(args))
        service.model.data.id = self._obj.id or 0
        return service


class ARDBAys(AYSable):

    def __init__(self, storageserver):
        self._obj = storageserver
        self.actor = 'ardb'

    def get(self, aysrepo):
        """
        get the AYS service
        """
        try:
            service = aysrepo.serviceGet(role=self.role, instance=self.name)
            service.model.data.bind = self._obj.bind or ''
            return service
        except j.exceptions.NotFound:
            raise ValueError("Could not find {} with name {}".format(self.role, self.name))

    def create(self, aysrepo):
        actor = aysrepo.actorGet(self.actor)
        args = {
            'homeDir': self._obj.data_dir,
            'bind': self._obj.bind,
            'master': self._obj.master.name if self._obj.master else '',
            'container': self._obj.container.name,
        }
        service = actor.serviceCreate(instance=self._obj.name, args=clean_dict(args))
        service.model.data.bind = self._obj.bind
        return service
