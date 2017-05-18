from JumpScale import j


class DNSClientFactory():

    def __init__(self):
        self.__jslocation__ = "j.clients.dns"

    def get(self, addr, port, login='root', password=None, sshkey_filename=None):
        executor = j.tools.executor.getSSHBased(
            addr=addr,
            port=port,
            login=login,
            passwd=password,
            key_filename=sshkey_filename)
        return executor.cuisine

    def getFromService(self, service):
        sshkey_path = None
        if 'sshkey' in service.producers:
            sshkey = service.producers['sshkey'][0]
            sshkey_path = j.sal.fs.joinPaths(sshkey.path, 'id_rsa')
        password = service.model.data.password if service.model.data.password != '' else None

        return self.get(
            addr=service.model.data.addr,
            port=service.model.data.port,
            login=service.model.data.login,
            password=password,
            sshkey_filename=sshkey_path)
