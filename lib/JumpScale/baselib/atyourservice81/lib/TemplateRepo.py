from JumpScale import j
from JumpScale.baselib.atyourservice81.lib.ActorTemplate import ActorTemplate
import asyncio
import threading
import inotify.adapters


def get_root_template_repo(path):
    template_repo = None
    if 'templates' in path:
        template_repo = path.split("templates")[0]
    elif 'tests' in path:
        template_repo = path.split("tests")[0]
    elif 'actorTemplates' in path:
        template_repo = path.split("actorTemplates")[0]
    return template_repo


def searchActorTemplates(path, is_global=False):
    """
    walk function that look recursively into 'path' after actor templates directories
    @returns: list of paths of directories containing actor tempaltes
    """
    res = set()
    actortemplatessearch = ""
    if not is_global:
        actortemplatessearch = " -or -wholename '*actorTemplates/*actions.py' -or -wholename '*actorTemplates/*schema.capnp' -or -wholename '*actorTemplates/*config.yaml'"
    cmd = """find %s \( -wholename '*templates/*actions.py' -or -wholename '*templates/*schema.capnp' -or -wholename '*templates/*config.yaml' -or -wholename '*tests/*actions.py' -or -wholename '*tests/*schema.capnp' -or -wholename '*tests/*config.yaml' %s \) -exec readlink -f {} \;""" % (path, actortemplatessearch)
    rc, out, err = j.sal.process.execute(cmd, die=False, showout=False)
    if rc == 0:
        return out.splitlines()
    return res


class TemplateRepoCollection:
    """
    Class reponsible for search/load tempates repos
    """

    def __init__(self):
        self.logger = j.logger.get('j.atyourservice')
        self._loop = asyncio.get_event_loop()  # TODO: question why do we need this
        self._template_repos = {}
        self._load()

    def _load(self):
        self.logger.info("reload actor templates repos")
        return self.__load(j.dirs.CODEDIR)

    def __load(self, path):
        for path in searchActorTemplates(path, is_global=True):
            template_repo = None
            if 'templates' in path:
                template_repo = path.split("templates")[0]
            elif 'tests' in path:
                template_repo = path.split("tests")[0]
            elif 'actorTemplates' in path:
                template_repo = path.split("actorTemplates")[0]

            template_repo_name = j.sal.fs.getBaseName(template_repo)
            if template_repo_name.startswith("_") or template_repo_name.startswith("."):
                continue
            self.create(path=template_repo)

        t = threading.Thread(target=self._watch_repos)
        t.start()

    def _watch_repos(self):
        mask = inotify.constants.IN_CLOSE_WRITE | inotify.constants.IN_MOVE | inotify.constants.IN_CREATE | inotify.constants.IN_DELETE | inotify.constants.IN_MODIFY
        i = inotify.adapters.InotifyTrees([d.encode() for d in [j.dirs.CODEDIR]], mask=mask)

        def delete_repo(repo_path):
            self.logger.info("actor template repo {} doesn't exists anymore, unload".format(repo_path))
            del(self._template_repos[repo_path])

        def create_repo(repo_path):
            self.create(path=repo_path)

        def update_repo(repo_path):
            self._templates[repo_path]._load()

        def handle_file(dirname, filename, event):
            if filename.endswith('.log'):
                return
            full_path = j.sal.fs.joinPaths(dirname, filename)
            is_file = j.sal.fs.isFile(full_path)
            # optimization to only react to these files
            if is_file and filename not in ['schema.capnp', 'config.yaml', 'actions.py']:
                return
            containing_repos = [i for i in self._template_repos if full_path.startswith(i)]
            inside_added_repo = bool(containing_repos)
            containing_repo = containing_repos[0] if inside_added_repo else None
            if inside_added_repo:
                if not is_it_a_template_repo(containing_repo):
                    delete_repo(containing_repo)
                else:
                    template_root = get_root_template_repo_if_relevant(dirname)
                    if template_root is None:
                        # not relevant
                        pass
                    elif template_root != containing_repo:
                        # This is evil
                        delete_repo(containing_repo)
                        create_repo(template_root)
                    else:
                        if is_file:
                            update_repo(template_root)
                        else:
                            cmd = """find %s \( -name schema.capnp -o -name config.yaml -o -name actions.py \) -print -quit""" % (path)
                            rc, _, _ = j.sal.process.execute(cmd, die=False, showout=False)
                            if rc != 0:
                                update_repo(template_root)
            else:
                template_root = get_root_template_repo_if_relevant(dirname)
                if template_root and template_root[0] in '._':
                    template_root = None
                if template_root:
                    create_repo(template_root)
                else:
                    self.__load(full_path)

        for event in i.event_gen():
            if event is not None:
                (header, type_names, dirname, filename) = event
                handle_file(dirname.decode(), filename.decode(), event)

    def list(self):
        # todo protect with lock
        return list(self._template_repos.values())

    def create(self, path, is_global=True):
        """
        path can be any path in a git repo
        will look for the directory with .git and create a TemplateRepo object if it doesn't exist yet
        """
        if path in self._template_repos:
            return self._template_repos[path]
        original_path = path

        while not j.sal.fs.exists(j.sal.fs.joinPaths(path, ".git")) and path != "":
            path = j.sal.fs.getParent(path).rstrip("/").strip()

        if path not in self._template_repos:
            if path == "":
                # did not find a git parent
                raise j.exceptions.NotFound("path '{}' and its parents is not a git repository".format(original_path))

            self.logger.debug("New template repos found at {}".format(path))
            self._template_repos[path] = TemplateRepo(path, is_global=is_global)

        return self._template_repos[path]

    # TEMPLATES
    # def actorTemplatesUpdate(self):
    #
    #     from IPython import embed
    #     print("DEBUG NOW 9898")
    #     embed()
    #     raise RuntimeError("stop debug here")
    #
    #     repos_path = (root for root, dirs, files in os.walk(path, followlinks=False) if '.ays' in files)
    #
    #     from IPython import embed
    #     print("DEBUG NOW 98989")
    #     embed()
    #     raise RuntimeError("stop debug here")
    #
    #     localGitRepos = j.clients.git.getGitReposListLocal()
    #
    #     # see if all specified ays templateRepo's are downloaded
    #     # if we don't have write permission on /opt don't try do download service templates
    #     codeDir = j.tools.path.get(j.dirs.CODEDIR)
    #     if codeDir.access(os.W_OK):
    #         # can access the opt dir, lets update the atyourservice
    #         # metadata
    #
    #         global_templates_repos = j.atyourservice.config['metadata']
    #
    #         for domain, info in global_templates_repos.items():
    #             url = info['url']
    #             if url.strip() == "":
    #                 raise j.exceptions.RuntimeError("url cannot be empty")
    #         branch = info.get('branch', 'master')
    #         templateReponame = url.rpartition("/")[-1]
    #         if templateReponame not in list(localGitRepos.keys()):
    #             j.do.pullGitRepo(url, dest=None, depth=1, ignorelocalchanges=False, reset=False, branch=branch)

    # def actorTemplatesUpdate(self, templateRepos):
    #     """
    #     update the git templateRepo that contains the service templates
    #     args:
    #         templateRepos : list of dict of templateRepos to update, if empty, all templateRepos are updated
    #                 {
    #                     'url' : 'http://github.com/account/templateRepo',
    #                     'branch' : 'master'
    #                 },
    #                 {
    #                     'url' : 'http://github.com/account/templateRepo',
    #                     'tag' : 'atag'
    #                 },
    #
    #     """
    #     for item in templateRepos:
    #         if 'branch' in item:
    #             branch = item["branch"]
    #         else:
    #             branch = "master"
    #         if 'tag' in item:
    #             tag = item["tag"]
    #         else:
    #             tag = ""
    #
    #         self.actorTemplateAdd(item["url"], branch=branch, tag=tag)
    #         j.do.pullGitRepo(url=templateRepo['url'], branch=branch, tag=tag)
    #
    #     self.reset()

    # @property
    # def actorTemplatesRepos(self):
    #     """
    #     find ays repos
    #     """
    #     if self._actorTemplatesRepos == {}:
    #         self.actorTemplates
    #     return self._actorTemplatesRepos


class TemplateRepo():
    """
    Represent git repository containing Actor templates
    """

    def __init__(self, path, is_global=True):
        self.logger = j.logger.get('j.atyourservice')
        self._loop = asyncio.get_event_loop()
        self.path = j.sal.fs.pathNormalize(path)
        self.git = j.clients.git.get(self.path, check_path=False)
        self.is_global = is_global
        self._templates = {}
        self._load()

    def _load(self):
        """
        path is absolute path (if specified)
        load the actor template in memory
        """
        actortemplates = set()
        for path in searchActorTemplates(self.path, is_global=self.is_global):
            if 'actions.py' in path:
                actortemplates.add(path.split("actions.py")[0])
            elif 'schema.capnp' in path:
                actortemplates.add(path.split("schema.capnp")[0])
            elif 'config.yaml' in path:
                actortemplates.add(path.split("config.yaml")[0])

        for path in actortemplates:

            actortemplate_name = j.sal.fs.getBaseName(path)
            if actortemplate_name.startswith("_") or actortemplate_name.startswith("."):
                continue
            templ = ActorTemplate(path=path, template_repo=self)
            self._templates[templ.name] = templ
        self.logger.info("reload actor templates from {}".format(self.path))

        # make sure all loaded repo still exists
        for template in list(self._templates.values()):
            if not j.sal.fs.exists(template.path):
                self.logger.info("template {} doesnt exists anymore, unload".format(template))
                del(self._templates[template.name])

    @property
    def templates(self):
        return list(self._templates.values())

    def find(self, name="", domain="", role=''):
        res = []
        for template in self._templates.values():
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

    def __str__(self):
        return "actor template repo: {}".format(self.path)

    def __repr__(self):
        return self.__str__()
