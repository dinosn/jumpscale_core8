
import struct
from SerializerBase import *

class SerializerBase64(SerializerBase):
    def __init__(self):
        self.__jslocation__ = "j.data.serializer.base64"

    def dumps(self,obj):
        return obj.encode("base64")

    def loads(self,s):
        return s.decode("base64")
