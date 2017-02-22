import g8core


class G8CoreFactory():

    def __init__(self):
        self.__jslocation__ = "j.clients.g8core"

    def get(self, host, port=6379, password=''):
        return g8core.Client(host=host, port=port, password=password)