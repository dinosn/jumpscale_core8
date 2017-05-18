from JumpScale import j
import logging


class JSLogger(logging.Logger):

    def __init__(self, name):
        super(JSLogger, self).__init__(name)
        self.custom_filters = {}

    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=1)

        """
        if self.isEnabledFor(logging.ERROR):
            eco = j.errorconditionhandler.getErrorConditionObject(
                ddict={}, msg=msg, msgpub=msg, category=self.name,
                level=logging.ERROR, type=logging.getLevelName(logging.ERROR),
                tb=None, tags='')
            j.errorconditionhandler._send2Redis(eco)

            self._log(logging.ERROR, msg, args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=1)
        """
        if self.isEnabledFor(logging.CRITICAL):
            eco = j.errorconditionhandler.getErrorConditionObject(
                ddict={}, msg=msg, msgpub=msg, category=self.name,
                level=logging.CRITICAL, type=logging.getLevelName(
                    logging.CRITICAL),
                tb=None, tags='')
            j.errorconditionhandler._send2Redis(eco)

            self._log(logging.CRITICAL, msg, args, **kwargs)
