from JumpScale.sal.g8os.abstracts import AYSable
from JumpScale import j


class StoragePoolAys(AYSable):

    def __init__(self, storagepool):
        self._obj = storagepool
        self._client = storagepool._client
        self.actor = 'storagepool'

    def create(self, aysrepo):
        try:
            service = aysrepo.serviceGet(role='storagepool', instance=self._obj.name)
        except j.exceptions.NotFound:
            service = None

        device_map, pool_status = self.get_devices_and_status()

        if service is None:
            # create new service
            actor = aysrepo.actorGet(self.actor)

            args = {
                'metadataProfile': self._obj.fsinfo['metadata']['profile'],
                'dataProfile': self._obj.fsinfo['data']['profile'],
                'devices': device_map,
                'node': self._node_name,
                'status': pool_status,
            }
            service = actor.serviceCreate(instance=self._obj.name, args=args)
        else:
            # update model on exists service
            service.model.data.init('devices', len(device_map))
            for i, device in enumerate(device_map):
                service.model.data.devices[i] = device

            service.model.data.status = pool_status
            service.saveAll()

        return service

    def get_devices_and_status(self):
        device_map = []
        disks = self._client.disk.list()['blockdevices']
        pool_status = 'healthy'
        for device in self._obj.devices:
            info = None
            for disk in disks:
                disk_name = "/dev/%s" % disk['kname']
                if device ==  disk_name and disk['mountpoint']:
                    info = disk
                    break
                for part in disk.get('children', []) or []:
                    if device == "/dev/%s" % part['kname']:
                        info = part
                        break
                if info:
                    break

            result = self._client.bash("smartctl -H %s > /dev/null ;echo $?" % disk_name).get()
            exit_status = int(result.stdout)
            status = 'healthy'

            if exit_status & 1 << 0:
                raise RuntimeError("Unable to get disk %s status" % disk_name)
            if (exit_status & 1 << 2) or (exit_status & 1 << 3):
                status = 'degraded'
                pool_status = 'degraded'

            device_map.append({
                'device': device,
                'partUUID': info['partuuid'] or '' if info else '',
                'status': status,
            })

        return device_map, pool_status

    @property
    def _node_name(self):
        def is_valid_nic(nic):
            for exclude in ['zt', 'core', 'kvm', 'lo']:
                if nic['name'].startswith(exclude):
                    return False
            return True

        for nic in filter(is_valid_nic, self._obj.node.client.info.nic()):
            if len(nic['addrs']) > 0 and nic['addrs'][0]['addr'] != '':
                return nic['hardwareaddr'].replace(':', '')
        raise AttributeError("name not find for node {}".format(self._obj.node))


class FileSystemAys(AYSable):

    def __init__(self, filesystem):
        self._obj = filesystem
        self.actor = 'filesystem'

    def create(self, aysrepo):
        actor = aysrepo.actorGet(self.actor)
        args = {
            'storagePool':self._obj.pool.name,
            'name': self._obj.name,
            # 'readOnly': ,FIXME
            # 'quota': ,FIXME
        }
        return actor.serviceCreate(instance=self._obj.name, args=args)

if __name__ == '__main__':
    from JumpScale import j
    j.atyourservice._start()
    repo = j.atyourservice.aysRepos.get('/opt/code/cockpit_repos/grid')
    node1 = j.sal.g8os.get_node('172.20.0.91')
    node2 = j.sal.g8os.get_node('172.20.0.92')
    cluster = j.sal.g8os.create_storagecluster('cluster1',[node1,node2],'hdd', 8, True)
    from IPython import embed;embed()
