
from JumpScale import j
import re

class CuisineNS():

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    
    def hostfile_get(self):
        """
        """
        result={}
        for line in self.cuisine.hostfile.splitlines():
            ipaddr_found = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',line)
            if ipaddr_found!=None:
                ipaddr_found=ipaddr_found.group()
                if ipaddr_found not in result:
                    result[ipaddr_found]=[]
                hosts=line.replace(ipaddr_found,"").strip().split(" ")
                for host in hosts:
                    if host.strip() not in result[ipaddr_found]:
                        result[ipaddr_found].append(host)
        result.pop("127.0.0.1","")
        result.pop('255.255.255.255',"")
        return result

    def hostfile_set_multiple(self,names=[],remove=[]):
        """
        @param names [[$ipaddr,$name]]
        """
        C="""
        127.0.0.1           localhost
        255.255.255.255     broadcasthost
        ::1                 localhost ip6-localhost ip6-loopback
        f02::1              ip6-allnodes
        ff02::2             ip6-allrouters
        """
        C=j.data.text.strip(C)
        res=self.hostfile_get()
        for item in remove:
            if item in res:
                res.pop(item)
        
        for ipaddr,name in names:
            if ipaddr not in res:
                res[ipaddr]=[]
            if name not in res[ipaddr]:
                res[ipaddr].append(name)

        for addr,names in res.items():
            # for name in names:
            names2=" ".join(names)
            C+="%-19s %s\n"%(addr,names2)

        #@todo need to do ipv6
        self.cuisine.hostfile=C

    def hostfile_set_fromlocal(self):
        """
        read local hostnames & transfer them to current cuisine
        """
        res=self.hostfile_get()
        local=j.tools.cuisine.get("")
        res2=local.ns.hostfile_get()
        for ipaddr,names in res2.items():
            for name in names:
                if ipaddr not in res:
                    res[ipaddr]=[]
                name=name.strip()
                if name not in res[ipaddr]:
                    res[ipaddr].append(name)

        res2send=[]
        for addr,names in res.items():
            for name in names:
                res2send.append([addr,name])

        self.hostfile_set_multiple(res2send)


    def hostfile_set(self,name,ipaddr):
        return self.hostfile_set_multiple([[ipaddr,name]])

    @property
    def nameservers(self):
        """
        can set & get
        @param nameservers [$nserver1,$nserver2]
        """        
        file = self.cuisine.core.file_read('/etc/resolv.conf')
        results = []
        for line in file.splitlines():
            nameserver = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',line)
            if nameserver:
                nameserver = nameserver.string.replace('nameserver', '').strip()
                results.append(nameserver)
        return results

    @nameservers.setter
    def nameservers(self, nameservers=[]):
        if not nameservers:
            raise ValueError('You need to provide at least one DNS server')
        if not isinstance(nameservers, list):
            raise ValueError('nameservers must be a list')

        content = '#EDITED BY JUMPSCALE NETWORK MANAGER\n'
        content += '#DO NOT EDIT THIS FILE BY HAND -- YOUR CHANGES WILL BE OVERWRITTEN\n'

        for ns in nameservers:
            content += 'nameserver %s\n' % ns
        self.file_write('/etc/resolv.conf', content)

