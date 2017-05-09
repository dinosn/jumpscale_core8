from JumpScale.sal.g8os.Node import Node
from JumpScale.sal.g8os.StorageCluster import StorageCluster
from JumpScale import j

class G8OSFactory(object):
    """Factory for G8OS SAL"""

    def __init__(self):
        self.__jslocation__ = "j.sal.g8os"
        self.logger = j.logger.get('j.sal.g8os')

    def get_node(self, addr, port=6379, password=None):
        """
        Returns a Node object that represent a G8OS node reachable
        at addr:port
        """
        return Node(
            addr=addr,
            port=port,
            password=password,
        )

    def create_storagecluster(self, label, nodes, disk_type, nr_server, has_slave=True):
        """
        @param label: string repsenting the name of the storage cluster
        @param nodes: list of node on wich we can deploy storage server
        @param disk_type: type of disk to be used by the storage server
        @param nr_server: number of storage server to deploy
        @param has_slave: boolean specifying of we need to deploy slave storage server
        """
        cluster = StorageCluster(label=label)
        cluster.create(nodes=nodes, disk_type=disk_type, nr_server=nr_server, has_slave=has_slave)
        return cluster


if __name__ == '__main__':
    from JumpScale import j
    node1 = j.sal.g8os.get_node('172.20.0.91')
    node2 = j.sal.g8os.get_node('172.20.0.92')
    cluster = j.sal.g8os.create_storagecluster('cluster1',[node1, node2],'hdd', 2, False)

    from IPython import embed;embed()
