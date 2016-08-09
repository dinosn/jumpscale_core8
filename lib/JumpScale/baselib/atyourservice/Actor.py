from JumpScale import j

# import JumpScale.baselib.actions
import copy
import inspect

from JumpScale.baselib.atyourservice.ActorTemplate import ActorTemplate


from JumpScale.baselib.atyourservice.Service import Service, loadmodule

DECORATORCODE = """
ActionMethodDecorator=j.atyourservice.getActionMethodDecorator()
ActionsBaseMgmt=j.atyourservice.getActionsBaseClassMgmt()

class action(ActionMethodDecorator):
    def __init__(self,*args,**kwargs):
        ActionMethodDecorator.__init__(self,*args,**kwargs)

"""


class ActorState():
    """
    is state object for actor, what was last state after installing
    """

    def __init__(self, Actor):
        self.Actor = Actor

        self._path = j.sal.fs.joinPaths(self.Actor.path, "state.json")
        if j.sal.fs.exists(path=self._path):
            self._model = j.data.serializer.json.load(self._path)
        else:
            self._model = {"methods": {}}

        self.changed = False
        self._changes = {}
        self._methodsList = []

        self.db = j.atyourservice.kvs.get("actor")

        if self.db.exists(self.hrkey) == False:
            self.saveToDB()

    def saveToDB(self):
        return
        from IPython import embed
        print("DEBUG NOW save2db")
        embed()
        model = j.atyourservice.AYSModel.Actor.new_message()
        model.role = self.name

        # resdb=j.atyourservice.db.get("Actor",self.Actor.name)

    def addMethod(self, name="", source="", isDefaultMethod=False):
        if source != "":
            if name in ["input", "init"]:
                if source.find("$(") != -1:
                    raise j.exceptions.Input(
                        "Action method:%s should not have template variable '$(...' in sourcecode for init or input method." % (self))

            if not isDefaultMethod:
                newhash = j.data.hash.md5_string(source)
                if name not in self._model["methods"] or newhash != self._model["methods"][name]:
                    self._changes[name] = True
                    self._model["methods"][name] = newhash
                    self.changed = True
            else:
                self._model["methods"][name] = ""

    def methodChanged(self, name):
        if name in self._changes:
            return True
        return False

    @property
    def methods(self):
        return self._model["methods"]

    @property
    def methodslist(self):
        """
        sorted methods
        """
        if self._methodsList == []:
            keys = sorted([item for item in self.methods.keys()])
            for key in keys:
                self._methodsList.append(self.methods[key])
        return self._methodsList

    def save(self):
        if self.changed:
            self.Actor.logger.info("Actor state Changed, writen to disk.")
            out = j.data.serializer.json.dumps(self._model, True, True)
            j.sal.fs.writeFile(filename=self._path, contents=out)
            # self.Actor.save2db()
            self.changed = False

    def __repr__(self):
        out = ""
        for item in self.methodslist:
            out += "%s\n" % item
        return out

    __str__ = __repr__


class Actor(ActorTemplate):

    def __init__(self, aysrepo, template):
        """
        """

        self.name = template.name
        self.role = self.name.split(".", 1)[0]

        self.template = template
        self.aysrepo = aysrepo

        self.domain = self.template.domain

        self.path = j.sal.fs.joinPaths(
            aysrepo.basepath, "actors", template.name)

        self.logger = j.atyourservice.logger

        self._init_props()

        # copy the files
        if not j.sal.fs.exists(path=self.path):
            self.copyFilesFromTemplate()

        self.state = ActorState(self)

# INIT

    def copyFilesFromTemplate(self):

        j.sal.fs.createDir(self.path)

        if j.sal.fs.exists(self.template.path_hrd_template):
            j.sal.fs.copyFile(self.template.path_hrd_template,
                              self.path_hrd_template)
        if j.sal.fs.exists(self.template.path_hrd_schema):
            j.sal.fs.copyFile(self.template.path_hrd_schema,
                              self.path_hrd_schema)
        if j.sal.fs.exists(self.template.path_actions_node):
            j.sal.fs.copyFile(self.template.path_actions_node,
                              self.path_actions_node)
        if j.sal.fs.exists(self.template.path_mongo_model):
            j.sal.fs.copyFile(self.template.path_mongo_model,
                              self.path_mongo_model)

        self._writeActionsFile()

    def _writeActionsFile(self):
        self._out = ""

        actionmethodsRequired = ["input", "init", "install", "stop", "start", "monitor", "halt", "check_up", "check_down",
                                 "check_requirements", "cleanup", "data_export", "data_import", "uninstall", "removedata", "consume"]

        if j.sal.fs.exists(self.template.path_actions):
            content = j.sal.fs.fileGetContents(self.template.path_actions)
        else:
            content = "class Actions(ActionsBaseMgmt):\n\n"

        if content.find("class action(ActionMethodDecorator)") != -1:
            raise j.exceptions.Input(
                "There should be no decorator specified in %s" % self.path_actions)

        content = "%s\n\n%s" % (DECORATORCODE, content)

        content = content.replace("from JumpScale import j", "")
        content = "from JumpScale import j\n\n%s" % content

        state = "INIT"
        amSource = ""
        amName = ""

        # DO NOT CHANGE TO USE PYTHON PARSING UTILS
        lines = content.splitlines()
        size = len(lines)
        i = 0

        while i < size:
            line = lines[i]
            linestrip = line.strip()
            if state == "INIT" and linestrip.startswith("class Actions"):
                state = "MAIN"
                i += 1
                continue

            if state == "MAIN" and linestrip.startswith("@"):
                if amSource != "":
                    self.state.addMethod(amName, amSource)
                amSource = ""
                amName = ""
                i += 1
                continue

            if state == "MAIN" and linestrip.startswith("def"):
                if amSource != "":
                    self.state.addMethod(amName, amSource)
                amSource = linestrip + "\n"
                amName = linestrip.split("(", 1)[0][4:].strip()
                # make sure the required method have the action() decorator
                if amName in actionmethodsRequired and not lines[i - 1].strip().startswith('@') and amName not in ["input"]:
                    lines.insert(i, '\n    @action()')
                    size += 1
                    i += 1

                i += 1
                continue

            if amName != "":
                amSource += "%s\n" % line[4:]
            i += 1

        # process the last one
        if amSource != "":
            self.state.addMethod(amName, amSource)

        content = '\n'.join(lines)

        # add missing methods
        for actionname in actionmethodsRequired:
            if actionname not in self.state.methods:
                am = self.state.addMethod(
                    name=actionname, isDefaultMethod=True)
                #not found
                if actionname == "input":
                    content += '\n\n    def input(self, service, name, role, instance, serviceargs):\n        return serviceargs\n'
                else:
                    content += "\n\n    @action()\n    def %s(self, service):\n        return True\n" % actionname

        j.sal.fs.writeFile(self.path_actions, content)

        for key, _ in self.state.methods.items():
            if self.state.methodChanged(key):
                self.logger.info("method:%s    %s changed" % (key, self))
                for service in self.aysrepo.findServices(templatename=self.name):
                    service.actions.change_method(service, methodname=key)
        self.state._changes = {}


# SERVICE
    def serviceActionsGet(self, service):
        modulename = "JumpScale.atyourservice.%s.%s" % (
            self.name, service.instance)
        mod = loadmodule(modulename, self.path_actions)
        return mod.Actions()

    def serviceCreate(self, instance="main", args={}, path='', parent=None, consume="", originator=None, model=None):
        """
        """
        if parent is not None and instance == "main":
            instance = parent.instance

        instance = instance.lower()

        service = self.aysrepo.getService(
            role=self.role, instance=instance, die=False)

        if service is not None:
            # print("NEWINSTANCE: Service instance %s!%s  exists." % (self.name, instance))
            service._Actor = self
            service.init(args=args)
            if model is not None:
                service.model = model
        else:
            key = "%s!%s" % (self.role, instance)

            if path:
                fullpath = path
            elif parent is not None:
                fullpath = j.sal.fs.joinPaths(parent.path, key)
            else:
                ppath = j.sal.fs.joinPaths(self.aysrepo.basepath, "services")
                fullpath = j.sal.fs.joinPaths(ppath, key)

            if j.sal.fs.isDir(fullpath):
                j.events.opserror_critical(msg='Service with same role ("%s") and of same instance ("%s") is already installed.\nPlease remove dir:%s it could be this is broken install.' % (
                    self.role, instance, fullpath))

            service = Service(aysrepo=self.aysrepo, Actor=self, instance=instance,
                              args=args, path="", parent=parent, originator=originator, model=model)

            self.aysrepo._services[service.key] = service

            # service.init(args=args)

        service.consume(consume)

        return service

    @property
    def services(self):
        """
        return a list of instance name for this template
        """
        services = self.aysrepo.findServices(templatename=self.name)
        return [service.instance for service in services]


# GENERIC
    def upload2AYSfs(self, path):
        """
        tell the ays filesystem about this directory which will be uploaded to ays filesystem
        """
        j.tools.sandboxer.dedupe(
            path, storpath="/tmp/aysfs", name="md", reset=False, append=True)

    def __repr__(self):
        return "Actor: %-15s" % (self.name)

    # def downloadfiles(self):
    #     """
    #     this method download any required files for this Actor as defined in the template.hrd
    # Use this method when building a service to have all the files ready to
    # sandboxing

    #     @return list of tuples containing the source and destination of the files defined in the Actoritem
    #             [(src, dest)]
    #     """
    #     dirList = []
    #     # download
    #     for Actoritem in self.hrd_template.getListFromPrefix("web.export"):
    #         if "dest" not in Actoritem:
    #             j.events.opserror_critical(msg="could not find dest in hrditem for %s %s" % (Actoritem, self), category="ays.ActorTemplate")

    #         fullurl = "%s/%s" % (Actoritem['url'],
    #                              Actoritem['source'].lstrip('/'))
    #         dest = Actoritem['dest']
    #         dest = j.application.config.applyOnContent(dest)
    #         destdir = j.sal.fs.getDirName(dest)
    #         j.sal.fs.createDir(destdir)
    #         # validate md5sum
    #         if Actoritem.get('checkmd5', 'false').lower() == 'true' and j.sal.fs.exists(dest):
    #             remotemd5 = j.sal.nettools.download(
    #                 '%s.md5sum' % fullurl, '-').split()[0]
    #             localmd5 = j.data.hash.md5(dest)
    #             if remotemd5 != localmd5:
    #                 j.sal.fs.remove(dest)
    #             else:
    #                 continue
    #         elif j.sal.fs.exists(dest):
    #             j.sal.fs.remove(dest)
    #         j.sal.nettools.download(fullurl, dest)

    #     for Actoritem in self.hrd_template.getListFromPrefix("git.export"):
    #         if "platform" in Actoritem:
    #             if not j.core.platformtype.myplatform.checkMatch(Actoritem["platform"]):
    #                 continue

    #         # pull the required repo
    #         dest0 = self.aysrepo._getRepo(Actoritem['url'], Actoritem=Actoritem)
    #         src = "%s/%s" % (dest0, Actoritem['source'])
    #         src = src.replace("//", "/")
    #         if "dest" not in Actoritem:
    #             j.events.opserror_critical(msg="could not find dest in hrditem for %s %s" % (Actoritem, self), category="ays.ActorTemplate")
    #         dest = Actoritem['dest']

    #         dest = j.application.config.applyOnContent(dest)
    #         src = j.application.config.applyOnContent(src)

    #         if "link" in Actoritem and str(Actoritem["link"]).lower() == 'true':
    #             # means we need to only list files & one by one link them
    #             link = True
    #         else:
    #             link = False

    #         if src[-1] == "*":
    #             src = src.replace("*", "")
    #             if "nodirs" in Actoritem and str(Actoritem["nodirs"]).lower() == 'true':
    #                 # means we need to only list files & one by one link them
    #                 nodirs = True
    #             else:
    #                 nodirs = False

    #             items = j.sal.fs.listFilesInDir(
    #                 path=src, recursive=False, followSymlinks=False, listSymlinks=False)
    #             if nodirs is False:
    #                 items += j.sal.fs.listDirsInDir(
    # path=src, recursive=False, dirNameOnly=False,
    # findDirectorySymlinks=False)

    #             raise RuntimeError("getshort_key does not even exist")
    #             items = [(item, "%s/%s" % (dest, j.sal.fs.getshort_key(item)), link)
    #                      for item in items]
    #         else:
    #             items = [(src, dest, link)]

    #         out = []
    #         for src, dest, link in items:
    #             delete = Actoritem.get('overwrite', 'true').lower() == "true"
    #             if dest.strip() == "":
    #                 raise j.exceptions.RuntimeError(
    #                     "a dest in codeActor cannot be empty for %s" % self)
    #             if dest[0] != "/":
    #                 dest = "/%s" % dest
    #             else:
    #                 if link:
    #                     if not j.sal.fs.exists(dest):
    #                         j.sal.fs.createDir(j.sal.fs.getParent(dest))
    #                         j.sal.fs.symlink(src, dest)
    #                     elif delete:
    #                         j.sal.fs.remove(dest)
    #                         j.sal.fs.symlink(src, dest)
    #                 else:
    #                     print(("copy: %s->%s" % (src, dest)))
    #                     if j.sal.fs.isDir(src):
    #                         j.sal.fs.createDir(j.sal.fs.getParent(dest))
    #                         j.sal.fs.copyDirTree(
    #                             src, dest, eraseDestination=False, overwriteFiles=delete)
    #                     else:
    #                         j.sal.fs.copyFile(
    #                             src, dest, True, overwriteFile=delete)
    #             out.append((src, dest))
    #             dirList.extend(out)

    #     return dirList
