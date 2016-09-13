from JumpScale import j

# from contextlib import redirect_stdout
# import io
# import imp
# import sys
import inspect
import capnp
# from JumpScale.baselib.atyourservice81.models.ServiceModel import ServiceModel
from collections import OrderedDict


def getProcessDicts(service, args={}):
    counter = 0

    defaults = {"prio": 10, "timeout_start": 10,
                "timeout_start": 10, "startupmanager": "tmux"}
    musthave = ["cmd", "args", "prio", "env", "cwd", "timeout_start",
                "timeout_start", "ports", "startupmanager", "filterstr", "name", "user"]

    procs = service.actor.hrd.getListFromPrefixEachItemDict("process", musthave=musthave, defaults=defaults, aredict=[
        'env'], arelist=["ports"], areint=["prio", "timeout_start", "timeout_start"])
    for process in procs:
        counter += 1

        process["test"] = 1

        if "name" not in process or process["name"].strip() == "":
            process["name"] = "%s_%s" % (service.name, service.instance)

        if service.actor.hrd.exists("env.process.%s" % counter):
            process["env"] = service.actor.hrd.getDict(
                "env.process.%s" % counter)

        if not isinstance(process["env"], dict):
            raise j.exceptions.RuntimeError("process env needs to be dict")

    return procs


class Service:

    def __init__(self, aysrepo, actor, name, args={}, model=None):
        """
        @param args, need to give it when you want to create a new instance
        """
        self.logger = aysrepo.logger
        self.aysrepo = aysrepo
        self.name = name
        self.actor = actor
        self._path = ""
        self._schema = None
        self._producers = None

        if j.data.types.string.check(actor):
            raise j.exceptions.RuntimeError("no longer supported, pass actor")

        if actor is None:
            raise j.exceptions.RuntimeError("service actor cannot be None")

        if name is None or name == "":
            raise j.exceptions.RuntimeError("name (ays instance name) needs to be specified")

        if model == None:
            res = self.aysrepo.db.service.find(actor=self.actor.name, name=self.name)
            if len(res) == 0:

                self.model = self.aysrepo.db.service.new()
                dbobj = self.model.dbobj
                dbobj.name = self.name

                if self.role == "" or self.name == "":
                    raise j.exceptions.Input(message="actor or name cannot be empty for service",
                                             level=1, source="", tags="", msgpub="")

                dbobj.actorName = self.actor.name
                dbobj.state = "new"

                dbobj.dataSchema = actor.model.dbobj.dataSchemaService

                self._data = j.data.capnp.getObj("aysi:%s!%s" % (self.actor.name, self.name),
                                                 dbobj.dataSchema, args=args, serializeToBinary=False)

                r = self.model.gitRepoAdd()
                r.url = self.aysrepo.git.remoteUrl

                # parents/producers

                skey = "%s!%s" % (self.role, self.name)
                if parent is not None:
                    relpath = j.sal.fs.joinPaths(parentobj.path, skey)
                else:
                    relpath = j.sal.fs.joinPaths("services", skey)

                r.path = relpath

                self.model.save()

                self.saveToFS()

                # service.processChange("init")
            else:
                # existing service
                self.model = self.aysrepo.db.service.find(name=name, actor=actor.name)
        else:
            self.model = model

        self.key = self.role + "!" + self.name  # human readable key

        # self._key = "%s!%s" % (self.role, self.name)
        # self._gkey = "%s!%s!%s" % (aysrepo.path, self.role, self.instance)

        # self.hrd

        # if actor is not None:
        #     self.model.actor = actor.name
        #     self.init(args=args)  # first time init
        #
        # # Set subscribed event into state
        # if self.actor.template.hrd is not None:
        #     for event, actions in self.actor.template.hrd.getDictFromPrefix('events').items():
        #         self.model.setEvents(event, actions)
        #     # Set recurring into state
        #     for action, period in self.actor.template.hrd.getDictFromPrefix('recurring').items():
        #         self.model.setRecurring(action, period)
        #
        #     # if service.hrd has remove some event action, update state to
        #     # reflect that
        #     actual = set(self.actor.template.hrd.getDictFromPrefix('events').keys())
        #     total = set(self.model.events.keys())
        #     for action in total.difference(actual):
        #         self.model.removeEvent(action)
        #
        #     # if service.hrd has remove some recurring action, update state to
        #     # reflect that
        #     actual = set(self.actor.template.hrd.getDictFromPrefix('recurring').keys())
        #     total = set(self.model.recurring.keys())
        #     for action in total.difference(actual):
        #         self.model.removeRecurring(action)
        #
        # self.model.save()

    def loadFromFS(self):
        """
        get content from fs and load in object
        only for DR purposes, std from key value stor
        """
        # TODO: *2 implement
        from IPython import embed
        print("DEBUG NOW loadFromFS")
        embed()
        raise RuntimeError("stop debug here")

        self.model.save()

    def saveToFS(self):
        j.sal.fs.createDir(self.path)
        path = j.sal.fs.joinPaths(self.path, "service.json")
        j.sal.fs.writeFile(filename=path, contents=str(self.model), append=False)

        ddict = self.data.to_dict()
        ddict2 = OrderedDict(ddict)
        # ddict = sortedcontainers.SortedDict(ddict)
        data3 = j.data.serializer.json.dumps(ddict2, sort_keys=True, indent=True)
        path3 = j.sal.fs.joinPaths(self.path, "data.json")
        j.sal.fs.writeFile(path3, data3)

    @property
    def schemaData(self):
        if self._schema is None:
            self._schema = j.data.capnp.getSchema("aysservice_%s" % self.actor.name, self.model.dbobj.capnpSchema)
        return self._schema

    @property
    def data(self):
        return self.schemaData.from_bytes_packed(self.model.dbobj.configData)

    def reset(self):
        self._hrd = None
        # self._yaml = None
        self._mongoModel = None
        self._dnsNames = []
        self._logPath = None
        self._state = None
        self._executor = None
        self._producers = None
        self._parentChain = None
        self._parent = None
        self._actor = None
        self._path = ""

    @property
    def role(self):
        return self.actor.name.split(".")[0]

    # @property
    # def key(self):
    #     return self.model.key

    @property
    def path(self):
        if self._path == "":
            relpath = self.model.dbobj.gitRepos[0].path
            assert self.model.dbobj.gitRepos[0].url == self.aysrepo.git.remoteUrl
            self._path = j.sal.fs.joinPaths(self.aysrepo.path, relpath)
        return self._path

    @property
    def dnsNames(self):
        raise NotImplemented("dns names in service")
        if self._dnsNames == []:
            self._dnsNames = self.hrd.getList("dns")
        return self._dnsNames

    @property
    def parents(self):
        raise NotImplemented("")
        # TODO: *1
        if self._parentChain is None:
            chain = []
            parent = self.parent
            while parent is not None:
                chain.append(parent)
                parent = parent.parent
            self._parentChain = chain
        return self._parentChain

    @property
    def parent(self):
        raise NotImplemented("")
        # TODO: *1
        if self._parent is None:
            if self.model.parent != "":
                self._parent = self.aysrepo.getServiceFromKey(
                    self.model.parent)
        return self._parent

    @property
    def hrd(self):
        if self._hrd is None:
            schema_path = j.sal.fs.joinPaths(self.path, 'schema.capnp')
            if not j.sal.fs.exists(schema_path):
                j.sal.fs.writeFile(schema_path, self.actor.schema.capnpSchema)
                capnp_models = capnp.load(schema_path)
                self._hrd = capnp_models.Schema.new_message()
        return self._hrd
        # if self._hrd == "EMPTY":
        # return None
        # if self._hrd is None:
        #     hrdpath = j.sal.fs.joinPaths(self.path, "instance.hrd")
        #     if not j.sal.fs.exists(path=hrdpath):
        #         self._hrd == "EMPTY"
        #         return None
        #     self._hrd = j.data.hrd.get(path=hrdpath, prefixWithName=False)

        # return self._hrd

    # def hrdCreate(self):
    #     hrdpath = j.sal.fs.joinPaths(self.path, "instance.hrd")
    #     self._hrd = j.data.hrd.get(path=hrdpath, prefixWithName=False)

    # @property
    # def model(self):
    #     if self._model is None:
    #         model_path = j.sal.fs.joinPaths(self.path, "model.yaml")
    #         if j.sal.fs.exists(model_path):
    #             self._model = j.data.serializer.yaml.loads(
    #                 j.sal.fs.fileGetContents(model_path))
    #     return self._model
    #
    # @model.setter
    # def model(self, model):
    #     self._hrd = "EMPTY"
    #     if j.data.types.dict.check(model):
    #         self._model = model
    #         model_path = j.sal.fs.joinPaths(self.path, "model.yaml")
    #         j.data.serializer.yaml.dump(model_path, model)
    #     else:
    #         raise NotImplementedError("only support yaml format at the moment")

    @property
    def producers(self):
        if self._producers is None:
            self._producers = {}
            for prod_model in self.model.producers:

                if prod_model.dbobj.actorName not in self._producers:
                    self._producers[prod_model.dbobj.actorName] = []

                result = self.aysrepo.servicesFind(name=prod_model.dbobj.name, actor=prod_model.dbobj.actorName)
                for service in result:
                    self._producers[prod_model.dbobj.actorName].append(service)

        return self._producers

    def remove_producer(self, role, instance):
        raise NotImplemented("")
        # TODO: *1
        key = "%s!%s" % (role, instance)
        self.model.remove_producer(role, instance)
        self._producers[role].remove(key)

    @property
    def executor(self):
        if self._executor is None:
            self._executor = self._getExecutor()
        return self._executor

    def save(self):
        self.model.save()

    # def update_hrd(self):
    #     if self.actor.template.schema is not None:
    #         self._hrd = self.actor.template.schema.hrdGet(hrd=self.hrd, args={})
    #         self._hrd.path = j.sal.fs.joinPaths(self.path, "instance.hrd")

    def processChange(self, item):
        pass

    def init(self, args={}):

        from IPython import embed
        print("DEBUG NOW init service ")
        embed()
        raise RuntimeError("stop debug here")
        self.logger.info('INIT service: %s' % self)

        # j.sal.fs.createDir(self.model.dbobj.origin.path)

        # TODO: call init action

        self.model.save()
        args = self.actions.input(self, self.actor, self.role, self.instance, args)

        originalhrd = j.data.hrd.get(content=str(self.hrd))

        # apply args
        if self._hrd == "EMPTY":
            self._hrd = None
        else:
            if self.actor.template.schema is not None:
                self._hrd = self.actor.template.schema.hrdGet(hrd=self.hrd, args=args)
                self._hrd.path = j.sal.fs.joinPaths(self.path, "instance.hrd")
            else:
                if args != {}:
                    for key, val in args.items():
                        if self.hrd.exists(key) and self.hrd.get(key) != val:
                            self.hrd.set(key, val)

        # self._action_methods = None  # to make sure we reload the actions

        if self.hrd is not None:
            self.hrd.save()
        self.model.save()
        self._consumeFromSchema(args)
        self.actions.init(service=self)

        if self.hrd is not None:
            newInstanceHrdHash = j.data.hash.md5_string(str(self.hrd))
            if self.model.instanceHRDHash != newInstanceHrdHash:
                self.actions.change_hrd_instance(
                    service=self, originalhrd=originalhrd)
                self.hrd.save()
            self.model.instanceHRDHash = newInstanceHrdHash

        if self.actor.template.hrd is not None:
            if self._hrd == "EMPTY":
                self._hrd = None
            newTemplateHrdHash = j.data.hash.md5_string(
                str(self.actor.template.hrd))
            if self.model.templateHRDHash != newTemplateHrdHash:
                # the template hash changed
                if self.hrd is not None:
                    self.hrd.applyTemplate(
                        template=self.actor.template.hrd, args={}, prefix='')
                    self.actions.change_hrd_template(
                        service=self, originalhrd=originalhrd)
                    self.hrd.save()
                    self.model.templateHRDHash = newTemplateHrdHash
        self.save()

    def _consumeFromSchema(self, args):

        if self.actor.schema is None:
            return

        self.logger.debug('[_consumeFromSchema] args %s' % args)

        # manipulate the HRD's to mention the consume's to producers
        consumes = self.actor.schema.consumeSchemaItemsGet()
        if consumes:
            for consumeitem in consumes:
                # parent exists
                role = consumeitem.consume_link
                consumename = consumeitem.name

                instancenames = []
                if consumename in args:
                    # args[consumename] can be a list or a string, we need to
                    # convert it to a list
                    if type(args[consumename]) == str:
                        instancenames = [args[consumename]]
                    else:
                        instancenames = args[consumename]

                ays_s = list()
                candidates = self.aysrepo.findServices(
                    role=consumeitem.consume_link)
                if len(candidates) > 0:
                    if len(instancenames) > 0:
                        ays_s = [
                            candidate for candidate in candidates if candidate.instance in instancenames]
                    else:
                        self.logger.debug(
                            '[_consumeFromSchema] No instance specificed for consumed service %s' % consumename)
                        ays_s = candidates

                # autoconsume
                if len(candidates) < int(consumeitem.consume_nr_min) and consumeitem.auto:
                    for instance in range(len(candidates), int(consumeitem.consume_nr_min)):
                        consumable = self.aysrepo.new(
                            name=consumeitem.consume_link, instance='auto_%i' % instance, parent=self.parent)
                        ays_s.append(consumable)

                if len(ays_s) > int(consumeitem.consume_nr_max):
                    raise j.exceptions.RuntimeError("Found too many services with role '%s' which we are relying upon for service '%s, max:'%s'" % (
                        role, self, consumeitem.consume_nr_max))
                if len(ays_s) < int(consumeitem.consume_nr_min):
                    msg = "Found not enough services with role '%s' which we are relying upon for service '%s, min:'%s'" % (
                        role, self, consumeitem.consume_nr_min)
                    if len(ays_s) > 0:
                        msg += "Require following instances:%s" % self.args[
                            consumename]
                    raise j.exceptions.RuntimeError(msg)

                # if producer has been removed from service, we need to remove
                # it from the state
                to_consume = set(ays_s)
                current_producers = self.producers.get(
                    consumeitem.consume_link, [])
                to_unconsume = set(current_producers).difference(to_consume)
                for ays in to_consume:
                    self.model.consume(aysi=ays)
                for ays in to_unconsume:
                    self.model.remove_producer(ays.role, ays.instance)
            self.model.save()

    def consume(self, input):
        """
        @input is comma separate list of ayskeys or a Service object or list of Service object

        ayskeys in format $domain|$name:$instance@role ($version)

        example
        ```
        @input $domain|$name!$instance,$name2!$instance2,$name2,$role4
        ```

        """
        if input is not None and input is not '':
            toConsume = set()
            if j.data.types.string.check(input):
                entities = [item for item in input.split(
                    ",") if item.strip() != ""]
                for entry in entities:
                    service = self.aysrepo.getServiceFromKey(entry.strip())
                    toConsume.add(service)

            elif j.data.types.list.check(input):
                for service in input:
                    toConsume.add(service)

            elif isinstance(input, Service):
                toConsume.add(input)
            else:
                raise j.exceptions.Input("Type of input to consume not valid. Only support list, string or Service object",
                                         category='AYS.consume', msgpub='Type of input to consume not valid. Only support list, string or Service object')

            for ays in toConsume:
                self.model.consume(aysi=ays)

    def getProducersRecursive(self, producers=set(), callers=set(), action="", producerRoles="*"):
        for role, producers2 in self.producers.items():
            for producer in producers2:
                if action == "" or producer.getAction(action) != None:
                    if producerRoles == "*" or producer.role in producerRoles:
                        producers.add(producer)
                producers = producer.getProducersRecursive(
                    producers=producers, callers=callers, action=action, producerRoles=producerRoles)
        return producers.symmetric_difference(callers)

    def printProducersRecursive(self, prefix=""):
        for role, producers2 in self.producers.items():
            # print ("%s%s"%(prefix,role))
            for producer in producers2:
                print("%s- %s" % (prefix, producer))
                producer.printProducersRecursive(prefix + "  ")

    def getProducersWaiting(self, action="install", producersChanged=set(), scope=None):
        """
        return list of producers which are waiting to be executing the action
        """

        # print ("producerswaiting:%s"%self)
        for producer in self.getProducersRecursive(set(), set()):
            # check that the action exists, no need to wait for other actions,
            # appart from when init or install not done

            if producer.state.getObject("init").state != "OK":
                producersChanged.add(producer)

            if producer.state.getObject("install").state != "OK":
                producersChanged.add(producer)

            if producer.getAction(action) is None:
                continue

            actionrunobj = producer.state.getSetObject(action)
            # print (actionrunobj)
            if actionrunobj.state != "OK":
                producersChanged.add(producer)

        if scope is not None:
            producersChanged = producersChanged.intersection(scope)

        return producersChanged

    def getNode(self):
        for parent in self.parents:
            if 'ssh' == parent.role:
                return parent
        return None

    def isOnNode(self, node=None):
        mynode = self.getNode()
        if mynode is None:
            return False
        return mynode.key == node.key

    def getTCPPorts(self, processes=None, *args, **kwargs):
        ports = set()
        if processes is None:
            processes = self.getProcessDicts()
        for process in self.getProcessDicts():
            for item in process.get("ports", []):
                if isinstance(item, str):
                    moreports = item.split(";")
                elif isinstance(item, int):
                    moreports = [item]
                for port in moreports:
                    if isinstance(port, int) or port.isdigit():
                        ports.add(int(port))
        return list(ports)

    def getPriority(self):
        processes = self.getProcessDicts()
        if processes:
            return processes[0].get('prio', 100)
        return 199

    def getProcessDicts(self, args={}):
        return getProcessDicts(self, args={})

    def _downloadFromNode(self):
        # if 'os' not in self.producers or self.executor is None:
        if not self.parent or self.parent.role != 'ssh':
            return

        hrd_root = "/etc/ays/local/"
        remotePath = j.sal.fs.joinPaths(
            hrd_root, j.sal.fs.getBaseName(self.path), 'instance.hrd')
        dest = self.path.rstrip("/") + "/" + "instance.hrd"
        self.logger.info("downloading %s '%s'->'%s'" %
                         (self.key, remotePath, self.path))
        self.executor.download(remotePath, self.path)

    def _getExecutor(self):
        executor = None
        tocheck = [self]
        tocheck.extend(self.parents)
        for service in tocheck:
            if hasattr(service.actions, 'getExecutor'):
                executor = service.actions.getExecutor(service=service)
                return executor
        return j.tools.executor.getLocal()

    def log(self, msg, level=0):
        self.action_current.log(msg)

    def listChildren(self):

        childDirs = j.sal.fs.listDirsInDir(self.path)
        childs = {}
        for path in childDirs:
            if path.endswith('__pycache__'):
                continue
            child = j.sal.fs.getBaseName(path)
            name, instance = child.split("!")
            if name not in childs:
                childs[name] = []
            childs[name].append(instance)
        return childs

    @property
    def children(self):
        res = []
        for key, service in self.aysrepo.services.items():
            if service.parent == self:
                res.append(service)
        return res

    def isConsumedBy(self, service):
        if self.role in service.producers:
            for s in service.producers[self.role]:
                if s.key == self.key:
                    return True
        return False

    def get_consumers(self):
        return [service for service in list(self.aysrepo.services.values()) if self.isConsumedBy(service)]

    def getProducers(self, producercategory):
        if producercategory not in self.producers:
            raise j.exceptions.Input(
                "cannot find producer with category:%s" % producercategory)
        instances = self.producers[producercategory]
        return instances

    def __eq__(self, service):
        if not service:
            return False
        if isinstance(service, str):
            return self.key == service
        return service.role == self.role and self.instance == service.instance

    def __hash__(self):
        return hash((self.instance, self.role))

    def __repr__(self):
        # return '%s|%s!%s(%s)' % (self.domain, self.name, self.instance,
        # self.version)
        return "%s!%s" % (self.role, self.name)
        # return self.key

    def __str__(self):
        return self.__repr__()

    @property
    def actions(self):
        return self.actor.get_actions(service=self)

    def runAction(self, action):
        a = self.getAction(action)
        if a is None:
            raise j.exceptions.Input(
                "Cannot find action:%s on %s" % (action, self))

        # when none means does not exist so does not have to be executed
        if a is not None:
            # if action not in ["init","input"]:
            return a(service=self)

    @property
    def action_methods(self):
        if self._action_methods is None:
            self._action_methods = {key: action for key, action in inspect.getmembers(
                self.actions, inspect.ismethod)}
        return self._action_methods

    def getAction(self, action):
        """
        @return None when not exist
        """
        if action not in self.action_methods:
            return None
        a = getattr(self.actions, action)
        return a

    def getActionSource(self, action):
        if action not in self.action_methods:
            return ""
        return j.data.text.strip(inspect.getsource(self.action_methods[action]))

    def _getDisabledProducers(self):
        producers = dict()
        for key, items in self.hrd.getDictFromPrefix("producer").items():
            producers[key] = [self.aysrepo.getServiceFromKey(
                item.strip(), include_disabled=True) for item in items]
        return producers

    def _getConsumers(self, include_disabled=False):
        consumers = list()
        services = j.atyourservice.findServices(
            include_disabled=True, first=False)
        for service in services:
            producers = service._getDisabledProducers(
            ) if include_disabled else service.producers
            if self.role in producers and self in producers[self.role]:
                consumers.append(service)
        return consumers

    def disable(self):
        self.stop()
        for consumer in self._getConsumers():
            candidates = self.aysrepo.findServices(role=self.role, first=False)
            if len(candidates) > 1:
                # Other candidates available. Should link consumer to new
                # candidate
                candidates.remove(self)
                candidate = candidates[0]
                producers = consumer.hrd.getList('producer.%s' % self.role, [])
                producers.remove(self.key)
                producers.append(candidate.key)
                consumer.hrd.set('producer.%s' % self.role, producers)
            else:
                # No other candidates already installed. Disable consumer as
                # well.
                consumer.disable()

        self.log("disable instance")
        self.model.hrd.set('disabled', True)

    def _canBeEnabled(self):
        for role, producers in list(self.producers.items()):
            for producer in producers:
                if producer.state.hrd.getBool('disabled', False):
                    return False
        return True

    def enable(self):
        # Check that all dependencies are enabled

        if not self._canBeEnabled():
            self.log(
                "%s cannot be enabled because one or more of its producers is disabled" % self)
            return

        self.model.hrd.set('disabled', False)
        self.log("Enable instance")
        for consumer in self._getConsumers(include_disabled=True):
            consumer.enable()
            consumer.start()

    def reload(self):
        # reload instance.hrd
        hrdpath = j.sal.fs.joinPaths(self.path, "instance.hrd")
        if not j.sal.fs.exists(path=hrdpath):
            self._hrd == "EMPTY"
        self._hrd = j.data.hrd.get(path=hrdpath, prefixWithName=False)

        # reload model if any
        model_path = j.sal.fs.joinPaths(self.path, "model.yaml")
        if j.sal.fs.exists(model_path):
            self._model = j.data.serializer.yaml.loads(
                j.sal.fs.fileGetContents(model_path))

        self.model.load()

    # @property
    # def action_methods_node(self):
    #     if self._action_methods_node is None or not self._rememberActions:
    #         if j.sal.fs.exists(path=self.actor.path_actions_node):
    #             action_methods_node = self._loadActions(self.actor.path_actions_node,"node")
    #         else:
    #             action_methods_node = j.atyourservice.getActionsBaseClassNode()()

    #         self._action_methods_node=action_methods_node

    #     return self._action_methods_node

    # def getAction(self, name, printonly=False):
    #     if name not in self._actionlog:
    #         action = self._setAction(name, printonly=printonly)
    #         print("new action:%s (get)" % action)
    #     else:
    #         action=self._actionlog[name]
    #     action.printonly = printonly
    #     self.action_current = action
    #     return action

    # def runAction(self,name,printonly=False):
    #     """
    #     look for action & run, there are no arguments
    #     """
    #     method=self._getActionMethodMgmt(name)
    #     if method==None:
    #         return None
    #     action=j.actions.add(method, kwargs={"ayskey":self.key}, die=True, stdOutput=False, \
    #             errorOutput=False, executeNow=True,force=True, showout=False, actionshow=True,selfGeneratorCode='selfobj=None')
    #     j.application.break_into_jshell("DEBUG NOW runaction")

    #     return action

    # def runActionNode(self,name,*args,**kwargs):
    #     """
    #     run on node, need to pass all arguments required
    #     there are no arguments given by default
    #     """
    #     method=self._getActionMethodNode(name)
    #     if method==None:
    #         return None
    #     j.application.break_into_jshell("DEBUG NOW runaction node")
    #     return action

    # def _getActionMethodMgmt(self,action):
    #     try:
    #         method=eval("self.action_methods_mgmt.%s"%action)
    #     except Exception as e:
    #         if str(e).find("has no attribute")!=-1:
    #             return None
    #         raise j.exceptions.RuntimeError(e)
    #     return method

    # def _getActionMethodNode(self,action):
    #     try:
    #         method=eval("self.action_methods_node.%s"%action)
    #     except Exception as e:
    #         if str(e).find("has no attribute")!=-1:
    #             return None
    #         raise j.exceptions.RuntimeError(e)
    #     return method

    # # ACTIONS
    # # def _executeOnNode(self, actionName, cmd=None, reinstall=False):
    # def _executeOnNode(self, actionName):
    #     if not self.parent or self.parent.role != 'ssh':
    #     # if 'os' not in self.producers or self.executor is None:
    #         return False
    #     self._uploadToNode()

    #     execCmd = 'source /opt/jumpscale8/env.sh; aysexec do %s %s %s' % (actionName, self.role, self.instance)

    #     executor = self.executor
    #     executor.execute(execCmd, die=True, showout=True)

    #     return True
