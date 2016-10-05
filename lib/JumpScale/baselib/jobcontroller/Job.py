from JumpScale import j
from JumpScale.core.errorhandling.ErrorConditionObject import ErrorConditionObject
import traceback
import importlib
import colored_traceback
from multiprocessing import Process, Queue
import pygments.lexers
from pygments.formatters import get_formatter_by_name
import cProfile

colored_traceback.add_hook(always=True)


class Job():
    """
    is what needs to be done for 1 specific action for a service
    """

    def __init__(self, model):
        self.logger = j.atyourservice.logger
        self.model = model
        self._action = None
        self._service = None
        self._source = None

    @property
    def action(self):
        if self._action is None:
            self._action = j.core.jobcontroller.db.action.get(self.model.dbobj.actionKey)
        return self._action

    @property
    def sourceToExecute(self):
        if self._source is None:
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
            s = s.replace("$args", self.action.argsText)
            self._source = s
        return self._source

    @property
    def sourceToExecutePath(self):
        path = j.sal.fs.joinPaths(j.dirs.tmpDir, "actions", self.action.dbobj.actorName, self.action.dbobj.name + ".py")
        j.sal.fs.createDir(j.sal.fs.joinPaths(j.dirs.tmpDir, "actions", self.action.dbobj.actorName))
        j.sal.fs.writeFile(path, self.sourceToExecute)
        return path

    def printLogs(self):
        logs = list()
        for log in self.model.dbobj.logs:
            logs.append(("{epoch} - {category}: {log}".format(
                epoch=j.data.time.epoch2HRDateTime(log.epoch),
                category=log.category,
                log=log.log
            )))
        logs = '\n'.join(logs)
        print (logs)
        return logs

    def save(self):
        self.model.save()

    @property
    def method(self):
        if self.action.key not in j.core.jobcontroller._methods:
            loader = importlib.machinery.SourceFileLoader(self.action.key, self.sourceToExecutePath)
            handle = loader.load_module(self.action.key)
            method = eval("handle.action")
            j.core.jobcontroller._methods[self.action.key] = method
        return j.core.jobcontroller._methods[self.action.key]

    @property
    def service(self):
        if self._service is None:
            # TODO: *3 is shortcut but will work for now, we need to see we are in right repo if multiple
            repo = [item for item in j.atyourservice._repos.items()][-1][1]
            serviceModel = repo.db.service.get(self.model.dbobj.serviceKey)
            self._service = serviceModel.objectGet(repo)
        return self._service

    def _processError(self, eco):
        logObj = self.model._logObjNew()

        if j.data.types.string.check(eco):
            # case it comes from the result of the processmanager
            eco = j.data.serializer.json.loads(eco)

            epoch = eco['epoch']
            if eco['_traceback'] != '':
                category = 'trace'
                msg = eco['_traceback']
            elif eco['errormessage'] != '':
                category = 'errormsg'
                msg = eco['errormessage']
            else:
                # TODO
                print("error message empty")
                import ipdb; ipdb.set_trace()

            level = int(eco['level'])
            tags = eco['tags']

        elif isinstance(eco, ErrorConditionObject):
            epoch = eco.epoch
            if eco._traceback != '':
                category = 'trace'
                msg = eco._traceback
            elif eco.errormessage != '':
                category = 'errormsg'
                msg = eco.errormessage
            else:
                # TODO
                print("error message empty")
                import ipdb; ipdb.set_trace()

            level = eco.level
            tags = eco.tags

        print(msg)
        self.model.log(
            msg=msg,
            level=level,
            category=category,
            epoch=epoch,
            tags=tags)

        self.model.save()

    def executeInProcess(self, service=None):
        """
        execute the job in the process, capture output when possible
        if debug job then will not capture output so our debugging features work
        """

        if self.model.dbobj.actorName != "":
            if service is None:
                service = self.service
            else:
                self._service = service

        service_action_obj = self.service.model.actions[self.model.dbobj.actionName]

        try:
            if self.model.dbobj.actorName != "":
                res = self.method(job=self)
            else:
                res = self.method(**self.model.args)

            service_action_obj.state = 'ok'
            self.model.dbobj.state = 'ok'

        except Exception as e:
            service_action_obj.state = 'error'
            self.model.dbobj.state = 'error'
            eco = j.errorconditionhandler.processPythonExceptionObject(e)
            self._processError(eco)
            raise j.exceptions.RuntimeError("could not execute job:%s" % self)

        self.model.result = res
        self.model.save()
        self.service.model.save()
        return res

    def execute(self):
        self.model.dbobj.state = 'running'

        # TODO improve debug detection
        debugInCode = self.sourceToExecute.find('ipdb') != -1 or self.sourceToExecute.find('IPython') != -1
        self.model.dbobj.debug = debugInCode

        # can be execute in paralle so we don't wait for end of execution here.
        if self.model.dbobj.debug:
            if self.model.dbobj.profile:
                pr = cProfile.Profile()
                pr.enable()

            process = self.executeInProcess()

            if self.model.dbobj.profile:
                pr.create_stats()
                stat_file = j.sal.fs.getTempFileName()
                pr.dump_stats(stat_file)
                self.model.dbobj.profileData = j.sal.fs.fileGetBinaryContents(stat_file)
                self.model.save()
                j.sal.fs.remove(stat_file)
        else:
            return j.core.processmanager.startProcess(self.method, {'job': self})

        return process

    def str_error(self, error):
        out = ''
        formatter = pygments.formatters.Terminal256Formatter(style=pygments.styles.get_style_by_name("vim"))

        if error.__str__() != "":
            out += "\n*TRACEBACK*********************************************************************************\n"
            # self.logger.error("\n*TRACEBACK*********************************************************************************\n")

            lexer = pygments.lexers.get_lexer_by_name("pytb", stripall=True)
            tb_colored = pygments.highlight(error.__str__(), lexer, formatter)
            print(tb_colored)
            out += tb_colored

        # self.logger.error("\n\n******************************************************************************************\n")
        out += "\n\n******************************************************************************************\n"
        return out

    def __repr__(self):
        out = "job: %s!%s (%s)\n" % (
            (self.model.dbobj.actorName, self.model.dbobj.serviceName, self.model.dbobj.actionName))
        return out

    __str__ = __repr__
