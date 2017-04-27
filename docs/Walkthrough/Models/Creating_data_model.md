# Creating data models and connecting them to different databases:
This walk-through explains how to create a model and how to traverse a collection.
this process compromises of three steps:

 - **Step 1** : creating the capnp schema
 - **Step 2** : creating the model file name_model.py
 - **Step 3** : creating the model collection file name_collection.py


 ## Step 1: Create  the capnp file
 To create the capnp schema:
 A capnp file with the fields required in the model is set. This is done Along with setting the types and  in some cases length of each field an  example of this is :
```capnp
@0xd80b12c2d2d132c34;

struct Issue {
    title @0 :Text;
    repo @1 :UInt16;
    milestone @2 :UInt32; #reference to key of Milestone
    assignees @3 :List(UInt32); #keys of user
    isClosed @4 :Bool;
    comments @5 :List(Comment);
    struct Comment{
        owner @0 :UInt32;
        content @1 :Text;
        id @2 :UInt32;
    }
    labels @6 :List(Text);
    content @7 :Text;
    id @8 :UInt32;
    source @9 :Text;
    #organization @10 :Text;  #key to organization , not sure??
    modTime @10 :UInt32;
    creationTime @11 :UInt32;
}
```
 this is stored as `model.capnp` withing the same directory that will contain the models directory as demonstrated
```
├── model.capnp
├── models
├    ├── __init__.py
├    ├── name_model.py
├    ├── name_collection.py
```




 ## Step 2: Create  the model file
 To create the model file , a python file and index has to be set to allow indexing , and
 unique identification of each instance of the model, as set below:
```python
from JumpScale import j

base = j.data.capnp.getModelBaseClass()


class OrgModel(base):
    """
    Model Class for an Issue object
    """

    @property
    def key(self):
        if self._key == "":
            self._key = j.data.hash.md5_string(self.dictJson)
        return self._key

    def index(self):
        # put indexes in db as specified
        ind = "%s:%s:%s" % (self.dbobj.name.lower(), str(self.dbobj.id),
                            self.dbobj.source.lower())
        self._index.index({ind: self.key})
        self._index.lookupSet("org_id", self.dbobj.id, self.key)
```

 ## Step 3: Create the collection file
 To create the collection , a python file has to be set to allow searching , and listing of the models, as seen bellow:

 ```python
 from JumpScale import j

 base = j.data.capnp.getModelBaseClassCollection()


 class UserCollection(base):
     """
     This class represent a collection of Issues
     """

     def list(self, name='', fullname='', email='', id=0, source="", returnIndex=False):
         """
         List all keys of repo model with specified params.

         @param name str,, name of user.
         @param fullname str,, full name of the user.
         @param email str,, email of the user.
         @param id int,, repo id in db.
         @param source str,, source of remote database.
         @param returnIndexalse bool,, return the index used.
         """
         if name == "":
             name = ".*"
         if fullname == "":
             fullname = ".*"
         if id == "" or id == 0:
             id = ".*"
         if source == "":
             source = ".*"
         if email == "":
             email = ".*"

         regex = "%s:%s:%s:%s:%s" % (name, fullname, email, str(id), source)
         return self._index.list(regex, returnIndex=returnIndex)

     def find(self, name='', fullname='', email='', id=0, source=""):
         """
         List all instances of repo model with specified params.

         @param name str,, name of user.
         @param fullname str,, full name of the user.
         @param email str,, email of the user.
         @param id int,, repo id in db.
         @param source str,, source of remote database.
         @param returnIndexalse bool,, return the index used.
         """
         res = []
         for key in self.list(name=name, fullname=fullname, email=email, id=id, source=source):
             res.append(self.get(key))
         return res

     def getFromId(self, id):
         key = self._index.lookupGet("issue_id", id)
         return self.get(key)

 ```

```
!!!
title = "Creating Data Model"
date = "2017-04-08"
tags = []
```
