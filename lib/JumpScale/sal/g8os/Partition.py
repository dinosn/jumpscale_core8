from JumpScale.sal.g8os.abstracts import Mountable


class Partition(Mountable):
    """Partition of a disk in a G8OS"""

    def __init__(self, disk, part_info):
        """
        part_info: dict returned by client.disk.list()
        """
        # g8os client to talk to the node
        self.disk = disk
        self._client = disk.node.client
        self.name = None
        self.size = None
        self.blocksize = None
        self.mountpoint = None
        self.uuid = None
        self._filesystems = []

        self._load(part_info)

    @property
    def filesystems(self):
        self._populate_filesystems()
        return self._filesystems

    @property
    def devicename(self):
        return "/dev/{}".format(self.name)

    def _load(self, part_info):
        self.name = part_info['name']
        self.size = int(part_info['size'])
        self.blocksize = self.disk.blocksize
        self.mountpoint = part_info['mountpoint']
        self.uuid = part_info['partuuid']

    def _populate_filesystems(self):
        """
        look into all the btrfs filesystem and populate
        the filesystems attribute of the class with the detail of
        all the filesystem present on the disk
        """
        self._filesystems = []
        for fs in (self._client.btrfs.list() or []):
            for device in fs['devices']:
                if device['path'] == "/dev/{}".format(self.name):
                    self._filesystems.append(fs)
                    break

    def __str__(self):
        return "Partition <{}>".format(self.name)

    def __repr__(self):
        return str(self)
