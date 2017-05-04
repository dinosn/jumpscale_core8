from collections import namedtuple
import re

Mount = namedtuple('Mount', ['device', 'mountpoint', 'fstype', 'options', 'dump', 'mpass'])


class MountInfoTool:
    def __init__(self):
        self.__jslocation__ = "j.tools.mountinfo"

    def parse(self, text):
        def unescape(match):
            # unescape spaces or other chars in /proc/mounts
            return chr(int(match.group()[1:], 8))
        # text retrieved by reading /proc/mounts.
        allmounts = []
        for mountline in text.splitlines():
            mount = mountline.split()
            for idx, option in enumerate(mount):
                mount[idx] = re.sub('\\\\0\d{2}', unescape, option)
            allmounts.append(Mount(*mount))
        return allmounts
