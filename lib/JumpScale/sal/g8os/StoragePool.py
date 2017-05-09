from JumpScale.sal.g8os.abstracts import Mountable
import os


def _prepare_device(node, devicename):
    j.sal.g8os.logger.debug("prepare device %s", devicename)
    ss = devicename.split('/')
    if len(ss) < 3:
        raise RuntimeError("bad device name: {}".format(devicename))
    name = ss[2]

    disk = node.disks.get(name)
    if disk is None:
        raise ValueError("device {} not found".format(name))

    if disk.partition_table is None:
        node.client.system('parted -s /dev/{} mklabel gpt mkpart primary 1m 100%'.format(name)).get()
        return node.disks.get(name).partitions[0]
    if len(disk.partitions) <= 0:
        disk.mkpart('1m', '100%')
    return disk.partitions[0]


class StoragePools:
    def __init__(self, node):
        self.node = node
        self._client = node._client

    def list(self):
        storagepools = []
        btrfs_list = self._client.btrfs.list()
        if btrfs_list:
            for btrfs in self._client.btrfs.list():
                if btrfs['label'].startswith('sp_'):
                    name = btrfs['label'].split('_', 1)[1]
                    devicenames = [device['path'] for device in btrfs['devices']]
                    storagepools.append(StoragePool(self.node, name, devicenames))
        return storagepools

    def get(self, name):
        for pool in self.list():
            if pool.name == name:
                return pool
        raise ValueError("Could not find StoragePool with name {}".format(name))

    def create(self, name, devices, metadata_profile, data_profile, overwrite=False):
        label = 'sp_{}'.format(name)
        j.sal.g8os.logger.debug("create storagepool %s", label)

        device_names = []
        for device in devices:
            part = _prepare_device(self.node, device)
            device_names.append(part.devicename)

        self._client.btrfs.create(label, device_names, metadata_profile, data_profile, overwrite=overwrite)
        pool = StoragePool(self.node, name, device_names)
        return pool


class StoragePool(Mountable):

    def __init__(self, node, name, devices):
        self.node = node
        self._client = node._client
        self.devices = devices
        self.name = name
        self._mountpoint = None
        self._ays = None

    @property
    def devicename(self):
        return 'UUID={}'.format(self.uuid)

    def mount(self, target=None):
        if target is None:
            target = os.path.join('/mnt/storagepools/{}'.format(self.name))
        return super().mount(target)

    def delete(self, zero=True):
        """
        Destroy storage pool
        param name: name of storagepool to delete
        param zero: write zeros (nulls) to the first 500MB of each disk in this storagepool
        """
        if self.mountpoint:
            self.umount()
        if zero:
            for device in self.devices:
                self._client.system('dd if=/dev/zero bs=1M count=500 of={}'.format(device))

    @property
    def mountpoint(self):
        disks = self._client.disk.list()['blockdevices']
        for device in self.devices:
            for disk in disks:
                if device == "/dev/%s" % disk['kname'] and disk['mountpoint']:
                    return disk['mountpoint']
                for part in disk.get('children', []) or []:
                    if device == "/dev/%s" % part['kname'] and part['mountpoint']:
                        return part['mountpoint']

    def is_device_used(self, device):
        """
        check if the device passed as argument is already part of this storagepool
        @param device: str e.g: /dev/sda
        """
        for d in self.devices:
            if d.startswith(device):
                return True
        return False

    def device_add(self, *devices):
        to_add = []
        for device in devices:
            if self.is_device_used(device):
                continue
            part = _prepare_device(self.node, device)
            j.sal.g8os.logger.debug("add device %s to %s", device, self)
            to_add.append(part.devicename)

        self._client.btrfs.device_add(self._get_mountpoint(), *to_add)
        self.devices.extend(to_add)

    def device_remove(self, *devices):
        self._client.btrfs.device_remove(self._get_mountpoint(), *devices)
        for device in devices:
            if device in self.devices:
                j.sal.g8os.logger.debug("remove device %s to %s", device, self)
                self.devices.remove(device)

    @property
    def fsinfo(self):
        if self.mountpoint is None:
            raise ValueError("can't get fsinfo if storagepool is not mounted")
        return self._client.btrfs.info(self.mountpoint)

    @mountpoint.setter
    def mountpoint(self, value):
        # do not do anything mountpoint is dynamic
        return

    def _get_mountpoint(self):
        mountpoint = self.mountpoint
        if not mountpoint:
            raise RuntimeError("Can not perform action when filesystem is not mounted")
        return mountpoint

    @property
    def info(self):
        for fs in self._client.btrfs.list():
            if fs['label'] == 'sp_{}'.format(self.name):
                return fs
        return None

    def raw_list(self):
        mountpoint = self._get_mountpoint()
        return self._client.btrfs.subvol_list(mountpoint) or []

    def list(self):
        subvolumes = []
        for subvol in self.raw_list():
            path = subvol['Path']
            type_, _, name = path.partition('/')
            if type_ == 'filesystems':
                subvolumes.append(FileSystem(name, self))
        return subvolumes

    def get(self, name):
        """
        Get Filesystem
        """
        for filesystem in self.list():
            if filesystem.name == name:
                return filesystem
        raise ValueError("Could not find filesystem with name {}".format(name))

    def exists(self, name):
        """
        Check if filesystem with name exists
        """
        for subvolume in self.list():
            if subvolume.name == name:
                return True
        return False

    def create(self, name, quota=None):
        """
        Create filesystem
        """
        j.sal.g8os.logger.debug("Create filesystem %s on %s", name, self)
        mountpoint = self._get_mountpoint()
        fspath = os.path.join(mountpoint, 'filesystems')
        self._client.filesystem.mkdir(fspath)
        subvolpath = os.path.join(fspath, name)
        self._client.btrfs.subvol_create(subvolpath)
        if quota:
            pass
        return FileSystem(name, self)

    @property
    def size(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs['devices']:
                total += device['size']
        return total

    @property
    def uuid(self):
        fs = self.info
        if fs:
            return fs['uuid']
        return None

    @property
    def used(self):
        total = 0
        fs = self.info
        if fs:
            for device in fs['devices']:
                total += device['used']
        return total

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale.sal.g8os.atyourservice.StoragePool import StoragePoolAys
            self._ays = StoragePoolAys(self)
        return self._ays

    def __repr__(self):
        return "StoragePool <{}>".format(self.name)


class FileSystem:
    def __init__(self, name, pool):
        self.name = name
        self.pool = pool
        self._client = pool.node.client
        self.path = os.path.join(self.pool.mountpoint, 'filesystems', name)
        self.snapshotspath = os.path.join(self.pool.mountpoint, 'snapshots', self.name)
        self._ays = None

    def delete(self, includesnapshots=True):
        """
        Delete filesystem
        """
        self._client.btrfs.subvol_delete(self.path)
        if includesnapshots:
            for snapshot in self.list():
                snapshot.delete()
            self._client.filesystem.remove(self.snapshotspath)

    def get(self, name):
        """
        Get snapshot
        """
        for snap in self.list():
            if snap.name == name:
                return snap
        raise ValueError("Could not find snapshot {}".format(name))

    def list(self):
        """
        List snapshots
        """
        snapshots = []
        if self._client.filesystem.exists(self.snapshotspath):
            for fileentry in self._client.filesystem.list(self.snapshotspath):
                if fileentry['is_dir']:
                    snapshots.append(Snapshot(fileentry['name'], self))
        return snapshots

    def exists(self, name):
        """
        Check if a snapshot exists
        """
        return name in self.list()

    def create(self, name):
        """
        Create snapshot
        """
        j.sal.g8os.logger.debug("create snapshot %s on %s", name, self.pool)
        snapshot = Snapshot(name, self)
        if self.exists(name):
            raise RuntimeError("Snapshot path {} exists.")
        self._client.filesystem.mkdir(self.snapshotspath)
        self._client.btrfs.subvol_snapshot(self.path, snapshot.path)
        return snapshot

    @property
    def ays(self):
        if self._ays is None:
            from JumpScale.sal.g8os.atyourservice.StoragePool import FileSystemAys
            self._ays = FileSystemAys(self)
        return self._ays

    def __repr__(self):
        return "FileSystem <{}: {!r}>".format(self.name, self.pool)


class Snapshot:
    def __init__(self, name, filesystem):
        self.filesystem = filesystem
        self._client = filesystem.pool.node.client
        self.name = name
        self.path = os.path.join(self.filesystem.snapshotspath, name)

    def rollback(self):
        self.filesystem.delete(False)
        self._client.btrfs.subvol_snapshot(self.path, self.filesystem.path)

    def delete(self):
        self._client.btrfs.subvol_delete(self.path)

    def __repr__(self):
        return "Snapshot <{}: {!r}>".format(self.name, self.filesystem)
