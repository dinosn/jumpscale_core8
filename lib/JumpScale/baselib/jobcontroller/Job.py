from JumpScale import j
import traceback
import colored_traceback

from multiprocessing import Process, Queue

colored_traceback.add_hook(always=True)

import pygments.lexers
from pygments.formatters import get_formatter_by_name

import importlib


class Job():
    """
    is what needs to be done for 1 specific action for a service
    """

    def __init__(self, model):
        self.logger = j.atyourservice.logger
        self.model = model
        self._action = None
        self._service = None

    @property
    def action(self):
        if self._action == None:
            self._action = j.core.jobcontroller.db.action.get(self.model.dbobj.actionKey)
        return self._action

    @property
    def sourceToExecute(self):
        s = """
        $imports
        from JumpScale import j

        def action($args):
        $source
        """
        s = j.data.text.strip(s)
        s = s.replace("$imports", '\n'.join(self.action.imports))
        code = self.action.dbobj.code
        code = j.data.text.indent(code, 4)

        s = s.replace("$source", code)
        # s = s.replace("$name", self.name)

        # argsstr = ""
        # for key, val in self.action.args.items():
        #     argsstr += "%s = %s," % (key, val)
        # argsstr = argsstr.rstrip(",")

        s = s.replace("$args", self.action.argsText)

        return s

    @property
    def sourceToExecutePath(self):
        path = j.sal.fs.joinPaths(j.dirs.tmpDir, "actions", self.action.dbobj.actorName, self.action.dbobj.name + ".py")
        j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.tmpDir, "actions", self.action.dbobj.actorName))
        j.do.writeFile(path, self.sourceToExecute)
        return path

    def save(self):
        self.model.save()

    @property
    def method(self):
        if not self.action.key in j.core.jobcontroller._methods:
            loader = importlib.machinery.SourceFileLoader(self.action.key, self.sourceToExecutePath)
            handle = loader.load_module(self.action.key)
            method = eval("handle.action")
            j.core.jobcontroller._methods[self.action.key] = method
        return j.core.jobcontroller._methods[self.action.key]

    @property
    def service(self):
        if self._service == None:
            # TODO: *3 is shortcut but will work for now, we need to see we are in right repo if multiple
            repo = [item for item in j.atyourservice._repos.items()][-1][1]
            serviceModel = repo.db.service.get(self.model.dbobj.serviceKey)
            self._service = serviceModel.getObject()
        return self._service

    def processError(self, eco):
        print(str(eco))
        # TODO: *1 need to put in job & save

    def executeInProcess(self, service=None):
        """
        execute the job in the process, capture output when possible
        if debug job then will not capture output so our debugging features work
        """

        if self.model.dbobj.actorName != "":
            if service == None:
                service = self.service
            else:
                self._service = service

        try:
            if self.model.dbobj.actorName != "":
                res = self.method(service, job=self)
            else:
                res = self.method(**self.model.args)
        except Exception as e:
            eco = j.errorconditionhandler.processPythonExceptionObject(e)
            self.processError(eco)
            raise j.exceptions.RuntimeError("could not execute job:%s" % self)

            # tb = e.__traceback__
            # value = e
            # type = None
            #
            # tblist = traceback.format_exception(type, value, tb)
            # tblist.pop(1)
            # self.traceback = "".join(tblist)
            #
            # err = ""
            # for e_item in e.args:
            #     if isinstance(e_item, (set, list, tuple)):
            #         e_item = ' '.join(e_item)
            #     err += "%s\n" % e_item
            # print("ERROR:%s" % err)
        self.model.result = res
        return res

    def execute(self):
        if self.model.dbobj.debug:
            return self.executeInProcess()
        else:
            from IPython import embed
            print("DEBUG NOW execute job")
            embed()
            raise RuntimeError("stop debug here")

    # def _str_error(self, error):
    #     out = ''
    #     formatter = pygments.formatters.Terminal256Formatter(
    #         style=pygments.styles.get_style_by_name("vim"))
    #
    #     if error.__str__() != "":
    #         out += "\n*TRACEBACK*********************************************************************************\n"
    #         # self.logger.error("\n*TRACEBACK*********************************************************************************\n")
    #
    #         lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)
    #         tb_colored = pygments.highlight(error.__str__(), lexer, formatter)
    #         print(tb_colored)
    #         out += tb_colored
    #
    #     # self.logger.error("\n\n******************************************************************************************\n")
    #     out += "\n\n******************************************************************************************\n"
    #     return out

    # def run(self):
    #     # for parallelized runs
    #     try:
    #         self.result = self.service.runAction(self.runstep.action)
    #         self.logger.debug('running stepaction: %s' % self.service)
    #         self.logger.debug('\tresult:%s' % self.result)
    #         self.result_q.put(self.result)
    #     except Exception as e:
    #         self.logger.debug(
    #             'running stepaction with error: %s' % self.service)
    #         self.logger.debug('\tresult:%s' % self.result)
    #         self.logger.debug('\error:%s' % self._str_error(e))
    #         self.error_q.put(self._str_error(e))
    #         self.result_q.put(self.result)
    #         raise e

    # def __repr__(self):
    #     out = "runstep action: %s!%s (%s)\n" % (
    #         self.service.key, self.name, self.state)
    #     if self.service_model != "":
    #         out += "model:\n%s\n\n" % j.data.text.indent(self.service_model)
    #     if self.service_hrd != "":
    #         out += "hrd:\n%s\n\n" % j.data.text.indent(self.service_hrd)
    #     if self.source != "":
    #         out += "source:\n%s\n\n" % j.data.text.indent(self.source)
    #     return out

    # __str__ = __repr__
