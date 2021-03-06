from JumpScale.clients.atyourservice.Client import Client
from JumpScale import j


class Factory:

    def __init__(self):
        self.__jslocation__ = "j.clients.atyourservice"

    def get(self, host='localhost', port=6379, unixsocket=None):
        return Client(host=host, port=port, unixsocket=unixsocket)

    def getFromConfig(self, config_path=None):
        if not config_path:
            host = j.atyourservice.config['redis'].get('host')
            port = j.atyourservice.config['redis'].get('port')
            unixsocket = j.atyourservice.config['redis'].get('unixsocket')
            return Client(host=host, port=port, unixsocket=unixsocket)
        cfg = j.data.serializer.yaml.load(config_path)
        if 'redis' not in cfg:
            raise j.exceptions.Input('format of the config file not valid. Missing redis section')

        redis = cfg['redis']
        return Client(host=redis.get('host', 'localhost'),
                      port=redis.get('port', 6379),
                      unixsocket=redis.get('unixsocket', None))
        return Client(unixsocket=j.atyourservice.config['redis']['unixsocket'])
