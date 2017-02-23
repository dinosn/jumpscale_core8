from JumpScale import j

base = j.data.capnp.getModelBaseClassCollection()

from peewee import *
from playhouse.sqlite_ext import Model

# from playhouse.sqlcipher_ext import *
# db = Database(':memory:')


class OrgCollection(base):
    """
    This class represent a collection of Orgs
    """

    def _init(self):
        # init the index
        db = j.tools.issuemanager.indexDB

        class Org(Model):
            key = CharField(index=True, default="")
            gogsRefs = CharField(index=True, default="")
            name = CharField(index=True, default="")
            description = CharField(index=True, default="")
            inGithub = BooleanField(index=True, default=False)
            members = CharField(index=True, default="")
            owners = CharField(index=True, default="")
            nrIssues = IntegerField(index=True, default=0)
            nrRepos = IntegerField(index=True, default=0)
            repos = CharField(index=True, default="")

            class Meta:
                database = j.tools.issuemanager.indexDB
                # order_by = ["id"]

        self.index = Org

        if db.is_closed():
            db.connect()
        db.create_tables([Org], True)

    def add2index(self, **args):
        """
        key = CharField(index=True, default="")
        gogsRefs = CharField(index=True, default="")
        name = CharField(index=True, default="")
        description = CharField(index=True, default="")
        inGithub = BooleanField(index=True, default=False)
        members = CharField(index=True, default="")
        owners = CharField(index=True, default="")
        nrIssues = IntegerField(index=True, default=0)
        nrRepos = IntegerField(index=True, default=0)
        repos = CharField(index=True, default="")

        @param args is any of the above

        members, owners and repos can be given as:
            can be "a,b,c"
            can be "'a','b','c'"
            can be ["a","b","c"]
            can be "a"

        """

        if "gogsRefs" in args:
            args["gogsRefs"] = ["%s_%s_%s" % (item["name"], item["id"], item['url']) for item in args["gogsRefs"]]

        args = self._arraysFromArgsToString(["members", "owners", "repos", "gogsRefs"], args)

        # this will try to find the right index obj, if not create

        obj, isnew = self.index.get_or_create(key=args["key"])

        for key, item in args.items():
            if key in obj._data:
                # print("%s:%s" % (key, item))
                obj._data[key] = item

        obj.save()

    def getFromGogsId(self, gogsName, gogsId, gogsUrl, createNew=True):
        return j.clients.gogs._getFromGogsId(self, gogsName=gogsName, gogsId=gogsId, gogsUrl=gogsUrl, createNew=createNew)
