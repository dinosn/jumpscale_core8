
# import JSModel
import time
from abc import ABCMeta, abstractmethod
from JumpScale import j
import collections

try:
    import snappy
except:
    rc, out = j.sal.process.execute("pip3 install python-snappy", die=True,
                                    outputToStdout=False, ignoreErrorOutput=False)
    import snappy


class KeyValueStoreBase:  # , metaclass=ABCMeta):
    '''KeyValueStoreBase defines a store interface.'''

    def __init__(self, name="", serializers=[], masterdb=None, cache=None, changelog=None):
        self.name = name
        self.logger = j.logger.get('j.servers.kvs')
        self.serializers = serializers or list()
        self.unserializers = list(reversed(self.serializers))
        self.cache = cache
        self.changelog = changelog
        self.masterdb = masterdb

    def __new__(cls, *args, **kwargs):
        '''
        Copies the doc strings (when available) from the base implementation
        '''

        attrs = iter(list(cls.__dict__.items()))

        for attrName, attr in attrs:
            if not attr.__doc__ and\
               hasattr(KeyValueStoreBase, attrName) and\
               not attrName.startswith('_')\
               and isinstance(attr, collections.Callable):

                baseAttr = getattr(KeyValueStoreBase, attrName)
                attr.__doc__ = baseAttr.__doc__

        return object.__new__(cls)

    def _encode(self, val, owner=None, expire=0, acl={}, schema=""):
        """
        @param expire is time in sec from now when object will expire
        @param is link to schema used to decode this object, is md5
        @param acl is dict of {secret:"rwd"}
        """
        # data = $type + $owner + $schema + $expire + $lengthsecretslist +
        # [secretslist] + snappyencoded(val) + $crcOfAllPrevious

        # type of this encoding, to make sure we have backwards compatibility
        # type = 4bits:  $schemaYesNo,$expireYesNo,0,0 + 4 bit version of format now 0
        ttype = 0

        ls = len(schema)
        if schema == None or schema = "":
            schema2 = b""
        elif ls == 32:
            schema2 = j.data.hash.hex2bin(schema)
            ttype += 0b1000000
        elif ls == 16:
            schema2 = schema
            ttype += 0b1000000
        else:
            raise j.exceptions.Input(message="schema needs to be md5 in string or bin format",
                                     level=1, source="", tags="", msgpub="")

        if expire != 0:
            expire = j.data.time.getTimeEpoch() + expire
            ttype += 0b0100000
        else:
            expire = "b"

        if owner is None:
            owner = j.application.owner
            if len(owner) != 16:
                raise j.exceptions.Input(message="owner needs to be 16 bytes", level=1, source="", tags="", msgpub="")

        ttype2 = ttype.to_bytes(1, byteorder='big', signed=False)

        nrsecrets = 0
        secrets2 = b""
        for secret, aclitem in acl.items():
            acl2 = 0
            if "r" in aclitem:
                acl2 += 0b10000000
            if "w" in aclitem:
                acl2 += 0b01000000
            if "d" in aclitem:
                acl2 += 0b00100000
            acl3 = acl2.to_bytes(1, byteorder='big', signed=False)
            if len(secret) == 32:
                secret = j.data.hash.hex2bin(secret)
            elif len(secret) != 16:
                raise j.exceptions.Input(message="secret needs to be 16 bytes", level=1, source="", tags="", msgpub="")
            nrsecrets += 1
            secrets2 += secret + acl3

        secrets3 = nrsecrets.to_bytes(2, byteorder='big', signed=False) + secrets2

        out2 = ttype + owner + schema2 + expire + secrets3 + snappy.compress(val)

        crc = j.data.hash.crc32_string(out2)
        crc2 = crc.to_bytes(4, byteorder='big', signed=False)
        out3 = out2 + crc2
        return out3

    def _decode(self, val):
        # TODO: *1 implement & test
        raise NotImplemented("")

    def set(self, key, value, category="", expire=0, secret="", acl={}, owner=None):

        value0 = self.get(key, secret=secret, category=category, decode=False)
        # verify will make sure that crc is checked
        owner, schema, expire, acl, value1 = self._decode(value0, verify=True)

        msg = "user with secret %s has no write permission on object:%s" % (secret, key)
        if secret in acl:
            if "w" not in acl[secret]:
                raise j.exceptions.Input(message=msg, level=1, source="", tags="", msgpub="")
        elif owner != secret"
            raise j.exceptions.Input(message=msg, level=1, source="", tags="", msgpub="")

        # now we know that secret has right to modify the object

        if schema != self.schemaId:
            raise j.exceptions.Input(
                message="schema of this db instance should be same as what is found in db", level=1, source="", tags="", msgpub="")

        # update acl with new one
        acl1 = acl.update(acl)

        value1 = self._encode(value, owner=owner, expire=expire, acl=acl1, schema=self.schemaId)

        if self.cache != None:
            self.cache._set(key=key, category=category, value=value1)

    def get(self, key, secret="", category="", verify=False, decode=True):
        '''
        Gets a key value pair from the store.

        @param: category of the key value pair
        @type: String

        @param: key of the key value pair
        @type: String

        @return: value of the key value pair
        @rtype: Objects
        '''
        if self.cache != None:
            res = self.cache._get(key=key, category=category)  # get raw data
            if res != None:
                return self.unserialize(self._decode(res))
        value1 = self._get(key=key, category=category)
        if value1 == None:
            return None
        if decode:
            value2 = self._decode(value1)
            value3 = self.unserialize(value2)
        else:
            value3 = value1

        if self.cache != None:
            self.cache._set(key=key, category=category, value=value1)

        return value3

        return self._get(key, secret, category)

    def delete(self, key, category="", secret=""):

        value0 = self.get(key, secret=secret, category=category, decode=False)
        # verify will make sure that crc is checked
        owner, schema, expire, acl, value1 = self._decode(value0, verify=False)

        msg = "user with secret %s has no write permission on object:%s" % (secret, key)
        if secret in acl:
            if "d" not in acl[secret]:
                raise j.exceptions.Input(message=msg, level=1, source="", tags="", msgpub="")
        elif owner != secret"
            raise j.exceptions.Input(message=msg, level=1, source="", tags="", msgpub="")

        self._delete(key=key, category=category)

# DO NOT LOOK AT BELOW RIGHT NOW IS FOR FUTURE

    def checkChangeLog(self):
        pass

    def serialize(self, value):
        for serializer in self.serializers:
            value = serializer.dumps(value)
        return value

    def unserialize(self, value):
        for serializer in self.unserializers:
            if value is not None:
                value = serializer.loads(value)
        return value

    def cacheSet(self, key, value, expirationInSecondsFromNow=120):
        ttime = j.data.time.getTimeEpoch()
        value = [ttime + expirationInSecondsFromNow, value]
        if key == "":
            key = j.data.idgenerator.generateGUID()
        self.set(category="cache", key=key, value=value)
        return key

    def cacheGet(self, key, deleteAfterGet=False):
        r = self.get("cache", key)
        if deleteAfterGet:
            self.delete("cache", key)
        return r[1]

    def cacheDelete(self, key):
        self.delete("cache", key)

    def cacheExists(self, key):
        return self.exists("cache", key)

    def cacheList(self):

        if "cache" in self.listCategories():
            return self.list("cache")
        else:
            return []

    def cacheExpire(self):
        now = j.data.time.getTimeEpoch()
        for key in self.list():
            expiretime, val = self.get(key)
            if expiretime > now:
                self.delete("cache", key)

    @abstractmethod
    def exists(self, category, key):
        '''
        Checks if a key value pair exists in the store.

        @param: category of the key value pair
        @type: String

        @param: key of the key value pair
        @type: String

        @return: flag that states if the key value pair exists or not
        @rtype: Boolean
        '''

    @abstractmethod
    def list(self, category, prefix):
        '''
        Lists the keys matching `prefix` in `category`.

        @param category: category the keys should be in
        @type category: String
        @param prefix: prefix the keys should start with
        @type prefix: String
        @return: keys that match `prefix` in `category`.
        @rtype: List(String)
        '''
        raise j.exceptions.NotImplemented("list is only supported on selected db's")

    @abstractmethod
    def listCategories(self):
        '''
        Lists the categories in this db.

        @return: categories in this db
        @rtype: List(String)
        '''

    @abstractmethod
    def _categoryExists(self, category):
        '''
        Checks if a category exists

        @param category: category to check
        @type category: String
        @return: True if the category exists, False otherwise
        @rtype: Boolean
        '''

    def lock(self, locktype, info="", timeout=5, timeoutwait=0, force=False):
        """
        if locked will wait for time specified
        @param locktype of lock is in style machine.disk.import  (dot notation)
        @param timeout is the time we want our lock to last
        @param timeoutwait wait till lock becomes free
        @param info is info which will be kept in lock, can be handy to e.g. mention why lock taken
        @param force, if force will erase lock when timeout is reached
        @return None
        """
        category = "lock"
        lockfree = self._lockWait(locktype, timeoutwait)
        if not lockfree:
            if force == False:
                raise j.exceptions.RuntimeError("Cannot lock %s %s" % (locktype, info))
        value = [self.id, j.data.time.getTimeEpoch() + timeout, info]
        encodedValue = j.data.serializer.json.dumps(value)
        self.settest(category, locktype, encodedValue)

    def lockCheck(self, locktype):
        """
        @param locktype of lock is in style machine.disk.import  (dot notation)
        @return result,id,lockEnd,info  (lockEnd is time when lock times out, info is descr of lock, id is who locked)
                       result is False when free, True when lock is active
        """
        if self.exists("lock", locktype):
            encodedValue = self.get("lock", locktype)
            try:
                id, lockEnd, info = j.data.serializer.json.loads(encodedValue)
            except ValueError:
                self.logger.error("Failed to decode lock value")
                raise ValueError("Invalid lock type %s" % locktype)

            if j.data.time.getTimeEpoch() > lockEnd:
                self.delete("lock", locktype)
                return False, 0, 0, ""
            value = [True, id, lockEnd, info]
            return value
        else:
            return False, 0, 0, ""

    def _lockWait(self, locktype, timeoutwait=0):
        """
        wait till lock free
        @return True when free, False when unable to free
        """
        locked, id, lockEnd, info = self.lockCheck(locktype)
        if locked:
            start = j.data.time.getTimeEpoch()
            if lockEnd + timeoutwait < start:
                # the lock was already timed out so is free
                return True

            while True:
                now = j.data.time.getTimeEpoch()
                if now > start + timeoutwait:
                    return False
                if now > lockEnd:
                    return True
                time.sleep(0.1)
        return True

    def unlock(self, locktype, timeoutwait=0, force=False):
        """
        @param locktype of lock is in style machine.disk.import  (dot notation)
        """
        lockfree = self._lockWait(locktype, timeoutwait)
        if not lockfree:
            if force == False:
                raise j.exceptions.RuntimeError("Cannot unlock %s" % locktype)
        self.delete("lock", locktype)

    def incrementReset(self, incrementtype, newint=0):
        """
        @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
        """
        self.set("increment", incrementtype, str(newint))

    def increment(self, incrementtype):
        """
        @param incrementtype : type of increment is in style machine.disk.nrdisk  (dot notation)
        """
        if not self.exists("increment", incrementtype):
            self.set("increment", incrementtype, "1")
            incr = 1
        else:
            rawOldIncr = self.get("increment", incrementtype)
            if not rawOldIncr.isdigit():
                raise ValueError("Increment type %s does not have a digit value: %s" % (incrementtype, rawOldIncr))
            oldIncr = int(rawOldIncr)
            incr = oldIncr + 1
            self.set("increment", incrementtype, str(incr))
        return incr

    def getNrRecords(self, incrementtype):
        if not self.exists("increment", incrementtype):
            self.set("increment", incrementtype, "1")
            incr = 1
        return int(self.get("increment", incrementtype))

    def settest(self, category, key, value):
        """
        if well stored return True
        """
        self.set(category, key, value)
        if self.get(category, key) == value:
            return True
        return False

    def _assertValidCategory(self, category):
        if not isinstance(category, str) or not category:
            raise ValueError('Invalid category, non empty string expected')

    def _assertValidKey(self, key):
        if not isinstance(key, str) or not key:
            raise ValueError('Invalid key, non empty string expected')

    def _assertExists(self, category, key):
        if not self.exists(category, key):
            errorMessage = 'Key value store doesnt have a value for key '\
                '"%s" in category "%s"' % (key, category)
            self.logger.error(errorMessage)
            raise KeyError(errorMessage)

    def _assertCategoryExists(self, category):
        if not self._categoryExists(category):
            errorMessage = 'Key value store doesn\'t have a category %s' % (category)
            self.logger.error(errorMessage)
            raise KeyError(errorMessage)

    def now(self):
        """
        return current time
        """
        return j.data.time.getTimeEpoch()

    def getModifySet(self, category, key, modfunction, **kwargs):
        """
        get value
        give as parameter to modfunction
        try to set by means of testset, if not succesfull try again, will use random function to maximize chance to set
        @param kwargs are other parameters as required (see usage in subscriber function)
        """
        counter = 0
        while counter < 30:
            data = self.get(category, key)
            data2 = modfunction(data)
            if self.settest(category, key, data2):
                break  # go out  of loop, could store well
            time.time.sleep(float(j.data.idgenerator.generateRandomInt(1, 10)) / 50)
            counter += 1
        return data2

    def subscribe(self, subscriberid, category, startid=0):
        """
        each subscriber is identified by a key
        in db there is a dict stored on key for category = category of this method
        value= dict with as keys the subscribers
        {"kristof":[lastaccessedTime,lastId],"pol":...}

        """
        if not self.exists("subscribers", category):
            data = {subscriberid: [self.now(), startid]}
        else:
            if startid != 0:
                if not self.exists(category, startid):
                    raise j.exceptions.RuntimeError(
                        "Cannot find %s:%s in db, cannot subscribe, select valid startid" % (category, startid))

                def modfunction(data, subscriberid, db, startid):
                    data[subscriberid] = [db.now(), startid]
                    return data

                self.getModifySet("subscribers", category, modfunction,
                                  subscriberid=subscriberid, db=self, startid=startid)

    def subscriptionGetNextItem(self, subscriberid, category, autoConfirm=True):
        """
        get next item from subscription
        returns
           False,None when no next
           True,the data when a next
        """
        if not self.exists("subscribers", category):
            raise j.exceptions.RuntimeError("cannot find subscription")
        data = self.get("subscribers", category)
        if subscriberid not in data:
            raise j.exceptions.RuntimeError("cannot find subscriber")
        lastaccesstime, lastid = data[subscriberid]
        lastid += 1
        if not self.exists(category, startid):
            return False, None
        else:
            return True, self.get(category, startid)
        if autoConfirm:
            self.subscriptionAdvance(subscriberid, category, lastid)
        return self.get(category, key)

    def subscriptionAdvance(self, subscriberid, category, lastProcessedId):

        def modfunction(data, subscriberid, db, lastProcessedId):
            data[subscriberid] = [db.now(), lastProcessedId]
            return data

        self.getModifySet("subscribers", category, modfunction, subscriberid=subscriberid,
                          db=self, lastProcessedId=lastProcessedId)

    def setDedupe(self, category, data):
        """
        will return unique key which references the data, if it exists or not
        """
        if data == "" or data == None:
            return ""
        if len(data) < 32:
            return data
        md5 = j.data.hash.md5_string(data)
        if not self.exists(category, md5):
            self.set(category, md5, data)
        return md5

    def getDedupe(self, category, key):
        if len(key) < 32:
            return key.encode()
        return self.get(category, key)
