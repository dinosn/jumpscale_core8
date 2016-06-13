import threading
from JumpScale import j
from Base import Base
from Base import replacelabels
from github.GithubObject import NotSet
from Milestone import RepoMilestone


class Issue(Base):
    def __init__(self, repo, ddict={}, githubObj=None):
        self.logger = j.logger.get('j.clients.github.issue')
        self.repo = repo
        self._ddict = ddict
        self._githubObj = githubObj
        self._comments = None
        if githubObj is not None:
            self.load()

        self._lock = threading.RLock()
        # self.todo

    @property
    def api(self):
        if self._githubObj is None:
            self._githubObj = self.repo.api.get_issue(self.number)
        return self._githubObj

    @property
    def ddict(self):
        if self._ddict == {}:
            # no dict yet, fetch from github
            self.load()
        # we lazy load the comments. so it's only loaded when accesses
        self._ddict['comments'] = self.comments
        return self._ddict

    @property
    def comments(self):
        if self._comments is not None:
            return self._comments

        with self._lock:
            if self._comments is None:
                self.logger.debug("Loading comments for issue: %s" % self.number)
                self._comments = []
                for comment in self.api.get_comments():
                    obj = {}
                    user = self.repo.client.getUserLogin(githubObj=comment.user)
                    obj["user"] = user
                    obj["url"] = comment.url
                    obj["id"] = comment.id
                    obj["body"] = comment.body
                    obj["time"] = j.data.time.any2HRDateTime(
                        [comment.last_modified, comment.created_at])
                    self._comments.append(obj)
        return self._comments

    @property
    def guid(self):
        return self.repo.fullname + "_" + str(self._ddict["number"])

    @property
    def number(self):
        return int(self._ddict["number"])

    @property
    def title(self):
        return self._ddict["title"]

    @property
    def body(self):
        return self._ddict["body"]

    @body.setter
    def body(self, val):
        self._ddict["body"] = val
        self.api.edit(body=self._ddict['body'])

    @property
    def time(self):
        return self._ddict["time"]

    @property
    def url(self):
        return self._ddict["url"]

    @property
    def assignee(self):
        return self._ddict["assignee"]

    @property
    def labels(self):
        #we return a copy so changing the list doesn't actually change the ddict value
        return self._ddict["labels"][:]

    @property
    def id(self):
        return self._ddict["id"]

    @labels.setter
    def labels(self, val):
        # check if all are already in labels, if yes nothing to do
        if len(val) == len(self._ddict["labels"]):
            self._ddict["labels"].sort()
            val.sort()
            if val == self._ddict["labels"]:
                return
        self._ddict["labels"] = val
        toset = [self.repo.getLabel(item) for item in self._ddict["labels"]]
        self.api.set_labels(*toset)

    @property
    def milestone(self):
        return self._ddict["milestone"]

    @property
    def state(self):
        states = []
        for label in self.labels:
            if label.startswith("state"):
                states.append(label)
        if len(states) == 1:
            return states[0][len("state"):].strip("_")
        elif len(states) > 1:
            self.state = "question"
        else:
            return ""

    @state.setter
    def state(self, val):
        return self._setLabels(val, "state")

    @property
    def isOpen(self):
        return self._ddict['open'] == True

    @property
    def type(self):
        items = []
        for label in self.labels:
            if label.startswith("type"):
                items.append(label)
        if len(items) == 1:
            return items[0].partition("_")[-1]

        return ""

    @type.setter
    def type(self, val):
        return self._setLabels(val, "type")

    @property
    def priority(self):
        items = []
        for label in self.labels:
            if label.startswith("priority"):
                items.append(label)
        if len(items) == 1:
            return items[0].partition("_")[-1]
        else:
            self.priority = "normal"
            return self.priority

    @priority.setter
    def priority(self, val):
        return self._setLabels(val, "priority")

    @property
    def process(self):
        items = []
        for label in self.labels:
            if label.startswith("process"):
                items.append(label)
        if len(items) == 1:
            return items[0][len("process"):].strip("_")
        else:
            return ""

    @process.setter
    def process(self, val):
        return self._setLabels(val, "process")

    def _setLabels(self, val, category):
        if val is None or val == '':
            return

        if val.startswith(category):
            _, _, val = val.partition('_')

        val = val.strip("_")
        val = val.lower()

        val = "%s_%s" % (category, val)

        if val not in self.repo.labelnames:
            self.repo.labelnames.sort()
            llist = ",".join(self.repo.labelnames)
            raise j.exceptions.Input(
                "Label needs to be in list:%s (is understood labels in this repo on github), now is: '%s'" %
                (llist, val))

        # make sure there is only 1
        labels2set = self.labels
        items = []
        for label in self.labels:
            if label.startswith(category):
                items.append(label)
        if len(items) == 1 and val in items:
            return
        for item in items:
            labels2set.pop(labels2set.index(item))
        if val is not None or val != "":
            labels2set.append(val)
        self.labels = labels2set

    def load(self):

        self._ddict = {}

        # check labels
        labels = [item.name for item in self.api.labels]  # are the names
        newlabels = []
        for label in labels:
            if label not in self.repo.labelnames:
                if label in replacelabels:
                    if replacelabels[label] not in newlabels:
                        newlabels.append(replacelabels[label])
            else:
                if label not in newlabels:
                    newlabels.append(label)

        if labels != newlabels:
            self.logger.info(
                "change label:%s for %s" %
                (labels, self.api.title))
            labels2set = [self.repo.getLabel(item) for item in newlabels]
            self.api.set_labels(*labels2set)
            labels = newlabels

        self._ddict["labels"] = labels
        self._ddict["id"] = self.api.id
        self._ddict["url"] = self.api.html_url
        self._ddict["number"] = self.api.number
        self._ddict['open'] = self.api.state == 'open'

        self._ddict["assignee"] = self.repo.client.getUserLogin(
            githubObj=self.api.assignee)
        self._ddict["state"] = self.api.state
        self._ddict["title"] = self.api.title

        self._ddict["body"] = self.api.body

        self._ddict["time"] = j.data.time.any2HRDateTime(
            [self.api.last_modified, self.api.created_at])

        self.logger.debug("LOAD:%s %s" % (self.repo.fullname, self._ddict["title"]))

        if self.api.milestone is None:
            self._ddict["milestone"] = ""
        else:
            ms = RepoMilestone(repo=self.repo, githubObj=self.api.milestone)
            self._ddict["milestone"] = "%s:%s" % (ms.number, ms.title)

    @property
    def todo(self):
        if "_todo" not in self.__dict__:
            todo = []
            if self.body is not None:
                for line in self.body.split("\n"):
                    if line.startswith("!! "):
                        todo.append(line.strip().strip("!! "))
            for comment in self.comments:
                for line in comment['body'].split("\n"):
                    if line.startswith("!! "):
                        todo.append(line.strip().strip("!! "))
            self._todo = todo
        return self._todo

    @property
    def isStory(self):
        if self.type == 'story' or self.story_name != '':
            return True
        return False

    @property
    def isTask(self):
        if self.type == 'task' or self.title.lower().endswith('task'):
            return True
        return False

    def move_to_repo(self, repo):
        self.logger.info("%s: move to repo:%s" % (self, repo))
        body = "Issue moved from %s\n\n" % self.api.url
        for line in self.api.body.splitlines():
            if line.startswith("!!") or line.startswith(
                    '### Tasks:') or line.startswith('### Part of Story'):
                continue
            body += "%s\n" % line
        assignee = self.api.assignee if self.api.assignee else NotSet
        labels = self.api.labels if self.api.labels else NotSet
        moved_issue = repo.api.create_issue(title=self.title, body=body,
                                            assignee=assignee, labels=labels)
        moved_issue.create_comment(self._create_comments_backlog())
        self.api.create_comment("Moved to %s" % moved_issue.url)
        self.api.edit(state='close')

    def _create_comments_backlog(self):
        out = "### backlog comments of '%s' (%s)\n\n" % (self.title, self.url)
        for comment in self.api.get_comments():
            if comment.body.find("!! move") != -1:
                continue
            date = j.data.time.any2HRDateTime(
                [comment.last_modified, comment.created_at])
            out += "from @%s at %s\n" % (comment.user.login, date)
            out += comment.body + "\n\n"
            out += "---\n\n"
        return out

    def __str__(self):
        return "issue:%s" % self.title

    __repr__ = __str__
