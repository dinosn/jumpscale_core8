from JumpScale import j


class Disks:
    """This class give you access to disk related actions from the kvm sal over cuisine"""

    def __init__(self, controller):
        self._controller = controller
        self._storage_controller =  j.sal.kvm.StorageController(controller)

    def create(self, pool, name, size=100, image_name=""):
        """
        create an empty disk we can attach

        @param pool string: name of the pool in wich create the disk. pool need to exists
        @param size int: in GB
        @param image_name string: base image to load on the disk. used this for boot disk
        """
        disk = j.sal.kvm.Disk(self._controller, pool, name, size, image_name)
        disk.create()

    def download_image(self, url, overwrite=False):
        """
        download an image from an url and store it on the system to be used a base image for disks
        """
        name = url.split('/')[-1]
        path = j.sal.fs.joinPaths(self._controller.base_path, 'images', name)
        self._controller.executor.cuisine.core.file_download(url, path, overwrite=True)

    def imgage_get_path(self, name):
        """
        return the path of the image named `name`
        """
        return j.sal.fs.joinPaths(self._controller.base_path, "images", name)
