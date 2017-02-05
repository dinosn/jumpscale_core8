from JumpScale import j

try:
    import ovh
except:
    j.do.execute("pip3 install ovh")
    import ovh

import time

class OVHServer:

    def __init__(self,ovhclient,name):
        self.ovhclient=ovhclient
        self.name=name

    def reload(self):
        from IPython import embed
        print ("DEBUG NOW kk")
        embed()
        raise RuntimeError("stop debug here")


class OVHClient:

    def __init__(self,appkey, appsecret,consumerkey="",endpoint='soyoustart-eu'):
        if consumerkey=="":
            client = ovh.Client(endpoint=endpoint)
            ck = client.new_consumer_key_request()
            ck.add_recursive_rules(ovh.API_READ_WRITE, '/')
        self.client = ovh.Client(
            endpoint=endpoint,
            application_key=appkey,
            application_secret=appsecret,
            consumer_key=consumerkey,
        )
        self.details={}
        self._installationTemplates=None
        self._sshKeys=None

    @property
    def installationTemplates(self):
        if self._installationTemplates==None:
            self._installationTemplates=self.client.get('/dedicated/installationTemplate')
        return self._installationTemplates

    @property
    def sshKeys(self):
        if self._sshKeys==None:
            self._sshKeys=self.client.get('/me/sshKey')
        return self._sshKeys

    def serversList(self):
        return self.client.get("/dedicated/server")

    def serverGetDetail(self,name,reload=False):
        if not name in self.details or reload:
            self.details[name]= self.client.get("/dedicated/server/%s"%name)
        return self.details[name]

    def serverGetInstallStatus(self,name):
        try:
            return self.client.get("/dedicated/server/%s/install/status"%name)
        except Exception as e:
            if "Server is not being installed or reinstalled at the moment" in str(e):
                return None
            else:
                raise e

    def serversGetDetail(self):
        res={}
        for item in self.serversList():
            res[item]=self.serverGetDetail(item)
        return res

    def cuisineGet(self,name):
        details=self.serverGetDetail(name)
        e=j.tools.executor.get(details["ip"])
        return e.cuisine

    def backupInit(self,name):
        try:
            self.client.post("/dedicated/server/%s/features/backupFTP"%name)
        except Exception as e:
            if "You already have a backupFTP" in str(e):
                print("backup init already done for %s"%name)
                return "ALREADYOK"
            else:
                raise e
        print("backup init ok for %s"%name)
        return "OK"

    def backupGet(self,name):
        try:
            res=self.client.get("/dedicated/server/%s/features/backupFTP"%name)
        except Exception as e:
            if "The requested object (backupFTP) does not exist" in str(e):
                print("backup was not inited yet for %s"%name)
                self.backupInit(name)
                res= self.client.get("/dedicated/server/%s/features/backupFTP"%name)
            else:
                raise e
        return res


    def cuisinesGet(self):
        """
        return all cuisine connections to all known servers

        returns [(name,cuisine),]
        """
        res=[]
        for name in self.serversList():
            details=self.serverGetDetail(name)
            e=j.tools.executor.get(details["ip"])
            res.append((name,e.cuisine))
        return res


    def serversWaitInstall(self):
        nrInstalling=1
        while nrInstalling>0:
            nrInstalling=0
            for item in self.serversList():
                status=self.serverGetInstallStatus(name=item)
                if status!=None:
                    print(item)
                    print(j.data.serializer.yaml.dumps(status))
                    print ("-------------")
                    nrInstalling+=1
            time.sleep(2)
        self.details={}
        print("INSTALL DONE")

    def serverInstall(self,name="",installationTemplate="ubuntu1604-server_64",sshKeyName="ovh",\
            useDistribKernel=True,noRaid=True,hostname="",wait=True):
        """
        if name == * then will install on all and names will be the name given by ovh

        """
        if installationTemplate not in self.installationTemplates:
            raise j.exceptions.Input(message="could not find install template:%s"%templateName, level=1, source="", tags="", msgpub="")
        if sshKeyName not in self.sshKeys:
            raise j.exceptions.Input(message="could not find sshKeyName:%s"%sshKeyName, level=1, source="", tags="", msgpub="")

        if name=="*":
            for item in self.serversList():
                self.serverInstall(name=item,wait=False)
            wait=True
        elif name=="":
            raise j.exceptions.Input(message="please specify name", level=1, source="", tags="", msgpub="")
        else:
            if hostname=="":
                hostname=name
            details={}
            details["installationTemplate"]=installationTemplate
            details["useDistribKernel"]=useDistribKernel
            details["noRaid"]=noRaid
            details["customHostname"]=hostname
            details["sshKeyName"]=sshKeyName

            try:
                self.client.post("/dedicated/server/%s/install/start"%name, details=details,templateName=installationTemplate)
            except Exception as e:
                if "A reinstallation is already in todo" in str(e):
                    print("INFO:%s:%s"%(name,e))
                    pass
                else:
                    raise e

        if wait:
            self.serversWaitInstall()

        if name =="":
            self.details={}
        else:
            if name in self.details:
                self.details.pop(name)

class OVHFactory:
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.clients.ovh"
        self.logger = j.logger.get('j.clients.ovh')
        self.connections = {}

    def get(self, appkey, appsecret,consumerkey="",endpoint='soyoustart-eu'):
        """
        Visit https://eu.api.soyoustart.com/createToken/

        IMPORTANT:
        for rights add get,post,put & delete rights
        for each of them put /*
        this will make sure you have all rights on all methods recursive

        to get your credentials

        endpoints:
            ovh-eu for OVH Europe API
            ovh-ca for OVH North-America API
            soyoustart-eu for So you Start Europe API
            soyoustart-ca for So you Start North America API
            kimsufi-eu for Kimsufi Europe API
            kimsufi-ca for Kimsufi North America API
            runabove-ca for RunAbove API

        """
        return OVHClient(appkey=appkey, appsecret=appsecret,consumerkey=consumerkey,endpoint=endpoint)
