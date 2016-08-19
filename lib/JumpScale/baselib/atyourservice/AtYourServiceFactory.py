from JumpScale import j

# from JumpScale.baselib.atyourservice.actor import actor
# from JumpScale.baselib.atyourservice.Service import Service, loadmodule
from JumpScale.baselib.atyourservice.ActorTemplate import ActorTemplate

from JumpScale.baselib.atyourservice.ActionsBase import ActionsBase
from JumpScale.baselib.atyourservice.ActionMethodDecorator import ActionMethodDecorator

from JumpScale.baselib.atyourservice.AtYourServiceRepo import AtYourServiceRepo

from JumpScale.baselib.atyourservice.AtYourServiceTester import AtYourServiceTester
from JumpScale.baselib.atyourservice.AtYourServiceDB import AtYourServiceDBFactory


import colored_traceback

import os


import sys
if "." not in sys.path:
    sys.path.append(".")


colored_traceback.add_hook(always=True)


class AtYourServiceFactory:

    def __init__(self):
        self.__jslocation__ = "j.atyourservice"

        self._init = False

        self._domains = []
        self._templates = {}
        self._templateRepos = {}
        self._repos = {}

        # self._sandboxer = None

        self._type = None

        self.indocker = False

        # self.sync = AtYourServiceSync()

        self.debug = j.core.db.get("atyourservice.debug") == 1

        self.logger = j.logger.get('j.atyourservice')

        self._test = None

        self.db = AtYourServiceDBFactory()

    def _doinit(self, force=False):

        if force:
            self.reset()

        if self._init is False:

            if j.sal.fs.exists(path="/etc/my_init.d"):
                self.indocker = True

            localGitRepos = j.do.getGitReposListLocal()

            # see if all specified ays templateRepo's are downloaded
            # if we don't have write permissin on /opt don't try do download service templates
            codeDir = j.tools.path.get(j.dirs.codeDir)
            if codeDir.access(os.W_OK):
                # can access the opt dir, lets update the atyourservice
                # metadata

                global_templates_repos = j.application.config.getDictFromPrefix("atyourservice.metadata")

                for domain in list(global_templates_repos.keys()):
                    url = global_templates_repos[domain]['url']
                    if url.strip() == "":
                        raise j.exceptions.RuntimeError("url cannot be empty")
                    branch = global_templates_repos[domain].get('branch', 'master')
                    templateReponame = url.rpartition("/")[-1]
                    if templateReponame not in list(localGitRepos.keys()):
                        j.do.pullGitRepo(url, dest=None, depth=1, ignorelocalchanges=False, reset=False, branch=branch)

            # load global templates
            for domain, repo_info in global_templates_repos.items():
                _, _, _, _, repo_path, _ = j.do.getGitRepoArgs(repo_info['url'])
                gitrepo = j.clients.git.get(repo_path, check_path=False)
                # self._templates.setdefault(gitrepo.name, {})
                for templ in self._actorTemplatesGet(gitrepo, repo_path):
                    self._templates[templ.name] = templ

            self._reposLoad()

            self._init = True

        self._init = True

    def reset(self):
        self._templateRepos = {}
        self._repos = {}
        self._domains = []
        self._templates = {}
        self._init = False


# TEMPLATES

    @property
    def actorTemplates(self):
        """
        these are actor templates usable for all ays templateRepo's
        """
        if self._templates == {}:
            self._doinit()
        return self._templates

    def actorTemplatesUpdate(self, templateRepos=[]):
        """
        update the git templateRepo that contains the service templates
        args:
            templateRepos : list of dict of templateRepos to update, if empty, all templateRepos are updated
                    {
                        'url' : 'http://github.com/account/templateRepo',
                        'branch' : 'master'
                    }
        """
        if len(templateRepos) == 0:
            metadata = j.application.config.getDictFromPrefix(
                'atyourservice.metadata')
            templateRepos = list(metadata.values())

        for templateRepo in templateRepos:
            branch = templateRepo[
                'branch'] if 'branch' in templateRepo else 'master'
            j.do.pullGitRepo(url=templateRepo['url'], branch=branch)

        self._doinit(True)

    def actorTemplatesFind(self, name="", domain="", role=''):
        res = []
        for template in self.actorTemplates:
            if not(name == "" or template.name == name):
                # no match continue
                continue
            if not(domain == "" or template.domain == domain):
                # no match continue
                continue
            if not (role == '' or template.role == role):
                # no match continue
                continue
            res.append(template)

        return res

    def _actorTemplatesGet(self, gitrepo, path="", result=[], aysrepo=None):
        """
        path is absolute path (if specified)
        this is used in factory as well as in repo code, this is the code which actually finds the templates
        """
        if path == "":
            path = gitrepo.path

        if not j.sal.fs.exists(path=path):
            raise j.exceptions.Input("Cannot find path for ays templates:%s" % path)

        dirname = j.sal.fs.getBaseName(path)

        # check if this is already an actortemplate dir, if not no need to recurse
        def isValidTemplate(path):
            tocheck = ['schema.hrd', 'service.hrd', 'actions_mgmt.py',
                       'actions_node.py', 'model.py', 'actions.py', "model.capnp"]
            dirname = j.sal.fs.getBaseName(path)
            for aysfile in tocheck:
                if j.sal.fs.exists('%s/%s' % (path, aysfile)):
                    if not dirname.startswith("_"):
                        return True
                    else:
                        return False
            return False

        if isValidTemplate(path):
            templ = ActorTemplate(gitrepo, path, aysrepo=aysrepo)
            if aysrepo == None:  # no need to check if in repo because then there can be doubles
                if templ.name in self._templates:
                    if path != self._templates[templ.name].path:
                        self.logger.debug('found %s in %s and %s' %
                                          (templ.name, path, self._templates[templ.name].path))
                        raise j.exceptions.Input("Found double template: %s" % templ.name)
            result.append(templ)
        else:
            # not ays actor so lets see for subdirs
            for servicepath in j.sal.fs.listDirsInDir(path, recursive=False):
                dirname = j.sal.fs.getBaseName(servicepath)
                if not dirname.startswith("."):
                    result = self._actorTemplatesGet(gitrepo, servicepath, result, aysrepo=aysrepo)

        return result

# REPOS

    def repoCreate(self, path):
        self._doinit()
        if j.sal.fs.exists(path):
            raise j.exceptions.Input("Directory %s already exists. Can't create AYS repo at the same location." % path)
        j.sal.fs.createDir(path)
        j.sal.fs.createEmptyFile(j.sal.fs.joinPaths(path, '.ays'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'actorTemplates'))
        j.sal.fs.createDir(j.sal.fs.joinPaths(path, 'blueprints'))
        j.tools.cuisine.local.core.run('git init')
        j.sal.nettools.download(
            'https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore', j.sal.fs.joinPaths(path, '.gitignore'))
        name = j.sal.fs.getBaseName(path)
        git_repo = j.clients.git.get(path)
        self._templateRepos[path] = AtYourServiceRepo(name=name, gitrepo=git_repo, path=path)
        print("AYS Repo created at %s" % path)
        return self._templateRepos[path]

    def _reposLoad(self, path=""):
        """
        load templateRepo's from path
        if path not specified then will go from current path, will first walk down if no .ays dirs found then will walk up to find .ays file

        """
        if path == "":
            path = j.sal.fs.getcwd()

        if j.sal.fs.exists(path=j.sal.fs.joinPaths(path, ".ays")):
            # are in root of ays dir
            self._repoLoad(path)
            return

        # WALK down, find repo's below
        res = (root for root, dirs, files in os.walk(path) if '.ays' in files)
        res = [str(item) for item in res]

        if len(res) == 0:
            # now walk up & see if we find .ays in dir above
            while path != "":
                if j.sal.fs.exists(path=j.sal.fs.joinPaths(path, ".ays")):
                    self._repoLoad(path)
                    return
                path = j.sal.fs.getParent(path)
                path = path.strip("/").strip()

        if len(res) == 0:
            # did not find ays dir up or down
            j.logger.log('No AYS repos found in %s. need to find a .ays file in root of aysrepo, did walk up & down' % path)
        #     raise j.exceptions.Input("Cannot find AYS repo in:%s, need to find a .ays file in root of aysrepo, did walk up & down." % path)

        # now load the repo's
        for path in res:
            self._repoLoad(path)

    def _repoLoad(self, path):

        if not j.sal.fs.exists(path=path):
            raise j.exceptions.Input("Cannot find ays templateRepo on path:%s" % path)
        gitpath = j.clients.git.findGitPath(path)
        gitrepo = j.clients.git.get(gitpath, check_path=False)

        name = j.sal.fs.getBaseName(path)

        if name in self._templateRepos:
            raise j.exceptions.Input(
                "AYS templateRepo with name:%s already exists at %s, cannot have duplicate names." % (name, path))

        self._repos[name] = AtYourServiceRepo(name, gitrepo, path)

    def repoGet(self, path="", name=""):
        """
        @return:    @AtYourServiceRepo object
        """
        self._doinit()
        if name is not "":
            if name not in self._repos:
                raise j.exceptions.Input(message="Could not find repo:%s" %
                                         name, level=1, source="", tags="", msgpub="")
            return self._repos[name]
        elif path is not "":
            for key, repo in self._repos.items():
                if repo.path == path:
                    return repo
            # repo does not exist yet
            self._repoLoad(path)
            for key, repo in self._repos.items():
                if repo.path == path:
                    return repo
            raise j.exceptions.Input(message="Could not find repo in path:%s" %
                                     path, level=1, source="", tags="", msgpub="")
        else:
            if len(self._repos.keys()) == 1:
                for key, item in self._repos.items():
                    return item
            else:
                raise j.exceptions.Input(
                    message="found more than 1 repo, cannot define which one to use", level=1, source="", tags="", msgpub="")

# FACTORY

    def getAYSTester(self, name="fake_IT_env"):
        self._init()
        return AtYourServiceTester(name)

    @property
    def domains(self):
        """
        actor domains
        """
        self._doinit()
        return self._domains

    def getActionsBaseClass(self):
        return ActionsBase

    def getActionMethodDecorator(self):
        return ActionMethodDecorator

    # def telegramBot(self, token, start=True):
    #     from JumpScale.baselib.atyourservice.telegrambot.TelegramAYS import TelegramAYS
    #     bot = TelegramAYS(token)
    #     if start:
    #         bot.run()
    #     return bot

    # def _parseKey(self, key):
    #     """
    #     @return (domain,name,instance,role)
    #     """
    #     key = key.lower()
    #     if key.find("|") != -1:
    #         domain, name = key.split("|")
    #     else:
    #         domain = ""
    #         name = key

    #     if name.find("@") != -1:
    #         name, role = name.split("@", 1)
    #         role = role.strip()
    #     else:
    #         role = ""

    #     if name.find("!") != -1:
    #         # found instance
    #         name, instance = name.split("!", 1)
    #         instance = instance.strip()
    #         if domain == '':
    #             role = name
    #             name = ''
    #     else:
    #         instance = ""

    #     name = name.strip()

    #     if role == "":
    #         if name.find('.') != -1:
    #             role = name.split(".", 1)[0]
    #         else:
    #             role = name

    #     domain = domain.strip()
    #     return (domain, name, instance, role)
