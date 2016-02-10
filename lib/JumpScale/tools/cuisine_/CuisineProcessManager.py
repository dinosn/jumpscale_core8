from JumpScale import j

#we implemented a fallback system if systemd does not exist
class ProcessManagerBase:

    def __init__(self,executor,cuisine):
        self.executor=executor
        self.cuisine=cuisine

    def get(self, pm = None):
        from ProcessManagerFactory import ProcessManagerFactory
        return ProcessManagerFactory.get(self.cuisine, pm)

class CuisineSystemd(ProcessManagerBase):
    def __init__(self,executor,cuisine):
        super().__init__(executor, cuisine)

    def list(self,prefix=""):
        """
        @return [[$name,$status]]
        """

        cmd='systemctl  --no-pager -l -t service list-unit-files'
        out=self.cuisine.run(cmd,showout=False)
        p = re.compile(u"(?P<name>[\S]*).service *(?P<state>[\S]*)")
        result=[]
        for line in out.split("\n"):
            res=re.search(p, line)
            if res!=None:
                # print (line)
                d=res.groupdict()
                if d["name"].startswith(prefix):
                    result.append([d["name"],d["state"]])
        else:
            from IPython import embed
            print ("DEBUG NOW list tmux")
            embed()

        return result

    def reload(self):
        self.cuisine.run("systemctl daemon-reload")

    def start(self,name):
        self.reload()
        # self.cuisine.run("systemctl enable %s"%name,showout=False)
        self.cuisine.run("systemctl enable %s"%name,die=False,showout=False)
        cmd="systemctl restart %s"%name
        self.cuisine.run(cmd,showout=False)

          

    def stop(self,name):
            cmd="systemctl disable %s"%name
            self.cuisine.run(cmd,showout=False,die=False)

            cmd="systemctl stop %s"%name
            self.cuisine.run(cmd,showout=False,die=False)
            

    def remove(self,prefix):
        self.stop()
        for name,status in self.systemd.list(prefix):
            self.systemd.stop(name)
            
            for item in self.cuisine.fs_find("/etc/systemd",True,"*%s.service"%name):
                print("remove:%s"%item)
                self.cuisine.file_unlink(item)
            self.cuisine.run("systemctl daemon-reload")

    def ensure(self,name,cmd="",env={},path="",descr="",systemdunit="", **kwargs):
        """
        Ensures that the given systemd service is self.cuisine.running, starting
        it if necessary and also create it
        @param systemdunit is the content of the file, will still try to replace the cmd
        """

        cmd=self.cuisine.args_replace(cmd)
        path=self.cuisine.args_replace(path)
        if cmd!="":
            if not cmd.startswith("/"):
                cmd0=cmd.split(" ",1)[0]
                cmd1=self.cuisine.bash.cmdGetPath(cmd0)
                cmd=cmd.replace(cmd0,cmd1)

            envstr = ""
            for name0, value in list(env.items()):
                envstr += "export %s=%s\n" % (name0, value)

            if envstr!="":
                cmd="%s;%s"%(envstr,cmd)

            cmd = cmd.replace('"', r'\"')

            if path:
                cwd = "cd %s;" % path
                if not cmd.startswith("."):
                    cmd="./%s"%cmd
                cmd = "%s %s" % (cwd, cmd)

           

            if systemdunit!="":
                C=systemdunit
            else:
                C="""
                [Unit]
                Description=$descr
                Wants=network-online.target
                After=network-online.target

                [Service]
                ExecStart=$cmd
                Restart=always

                [Install]
                WantedBy=multi-user.target
                """
            C=C.replace("$cmd",cmd)
            if descr=="":
                descr=name
            C=C.replace("$descr",descr)

            self.cuisine.file_write("/etc/systemd/system/%s.service"%name,C)

            self.cuisine.run("systemctl daemon-reload;systemctl restart %s"%name)
            self.cuisine.run("systemctl enable %s"%name,die=False,showout=False)
        else:
            self.start(name)
            
    def startAll(self):
        if self.systemdOK:
            #@todo (*1*) start all cuisine services
            raise RuntimeError("not implemented, please do")
        else:            
            for key in j.core.db.hkeys("processcmds"):
                key=key.decode()
                cmd=j.core.db.hget("processcmds",key).decode()
                self.start(key)



class CuisineRunit(ProcessManagerBase):
    def __init__(self,executor,cuisine):
        super().__init__(executor, cuisine)

    def list(self,prefix=""):
        for fs_find("/etc/service", recursive=False).split(",")
        res = self.cuisine.run("tmux lsw")



    def ensure(self, name, cmd="", env={}, path="", descr=""):
        """Ensures that the given upstart service is self.running, starting
        it if necessary."""
        if self.cuisine.file_exists("/etc/service/%s/run" %name ):
            cmd=self.cuisine.args_replace(cmd)
            path=self.cuisine.args_replace(path)


            envstr = ""
            for name0, value in list(env.items()):
                envstr += "export %s=%s\n" % (name0, value)

            if envstr!="":
                cmd="%s;%s"%(envstr,cmd)

            cmd = cmd.replace('"', r'\"')

            if path:
                cwd = "cd %s;" % path
                if not cmd.startswith("."):
                    cmd="./%s"%cmd
                cmd = "%s %s" % (cwd, cmd)

            # j.core.db.hset("processcmds",name,cmd)
            sv_text ="""#!/bin/sh
set -e
echo $descr
cd $path
exec $cmd
            """
            sv_text=sv_text.replace("$cmd",cmd)
            if descr=="":
                descr=name
            sv_text=sv_text.replace("$descr",descr)
            sv_text=sv_text.replace("$path",path)

            self.cuisine.file_link( "/etc/getty-5", "/etc/service")
            self.cuisine.dir_ensure("/etc/service/%s" %name)
            self.cuisine.file_attribs("/etc/service/%s/run" %name, "+x")
            self.cuisine.file_write("/etc/service/%s/run" %name, sv_text)

            self.start(name)
                
    def remove(self, prefix):
        """removes process from init"""
        if self.cuisine.file_exists("/etc/service/%s/run" %prefix ):
            self.stop(prefix)
            self.cuisine.dir_remove("/etc/service/%s/run" %prefix)         
                



    def reload(self, name):
        """Reloads the given service, or starts it if it is not self.running."""
        if self.cuisine.file_exists("/etc/service/%s/run" %name ):
            self.cuisine.run("sv reload %s" %name)


    def start(self, name):
        """Tries a `restart` command to the given service, if not successful
        will stop it and start it. If the service is not started, will start it."""
        if self.cuisine.file_exists("/etc/service/%s/run" %name ):
            self.cuisine.run("sv -w 15 start /etc/service/%s/" %name )

    def stop(self, name, **kwargs):
        """Ensures that the given upstart service is stopped."""
        if self.cuisine.file_exists("/etc/service/%s/run" %name):
            self.cuisine.run("sv -w 15 stop /etc/service/%s/" %name)

class CuisineTmuxec(ProcessManagerBase):
    def __init__(self,executor,cuisine):
        super().__init__(executor, cuisine)

    def list(self,prefix=""):
        self.cuisine.run("tmux lsw")
        
    def ensure(self, name, cmd="", env={}, path="", descr=""):
        """Ensures that the given upstart service is self.running, starting
        it if necessary."""
        cmd=self.cuisine.args_replace(cmd)
        path=self.cuisine.args_replace(path)

        if cmd=="":
            cmd=j.core.db.hget("processcmds",name).decode()
        else:
            envstr = ""
            for name0, value in list(env.items()):
                envstr += "export %s=%s\n" % (name0, value)

            if envstr!="":
                cmd="%s;%s"%(envstr,cmd)

            cmd = cmd.replace('"', r'\"')

            if path:
                cwd = "cd %s;" % path
                if not cmd.startswith("."):
                    cmd="./%s"%cmd
                cmd = "%s %s" % (cwd, cmd)

            j.core.db.hset("processcmds",name,cmd)

        self.stop(name)
        self.cuisine.tmux.executeInScreen("main", name, cmd, wait=True, reset=False)  

    def reload(self, name):
        """Reloads the given service, or starts it if it is not self.running."""
        cmd=j.core.db.hget("processcmds",name).decode()
        self.stop(name)
        self.cuisine.tmux.executeInScreen("main", name, cmd, wait=True, reset=False)

    def start(self, name):
        """Tries a `restart` command to the given service, if not successful
        will stop it and start it. If the service is not started, will start it."""
        cmd=j.core.db.hget("processcmds",name).decode()
        self.stop(name)
        self.cuisine.tmux.executeInScreen("main", name, cmd, wait=True, reset=False)


    def stop(self, name):
        """Ensures that the given upstart service is stopped."""
        self.cuisine.tmux.killWindow("main",name)

    def remove(self, name):
        """removes service """
        j.core.db.hdel("processcmds",name)









