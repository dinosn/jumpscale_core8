from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineCaddy(app):

    NAME = "caddy"

    @property
    def builddir(self):
        return j.sal.fs.joinPaths(self.core.dir_paths['BUILDDIR'], "caddy")

    def build(self):
        """
        Get/Build the binaries of caddy itself.
        """
        caddy_url = 'https://github.com/mholt/caddy/releases/download/v0.9.4/caddy_linux_amd64.tar.gz'
        dest = j.sal.fs.joinPaths(self.builddir, 'caddy_linux_amd64.tar.gz')
        self.cuisine.core.file_download(caddy_url, dest)
        self.cuisine.core.run('cd {builddir}; tar xvf {builddir}/caddy_linux_amd64.tar.gz'.format(builddir=self.builddir))

    def install(self, ssl=False, start=True, dns=None, reset=False, wwwrootdir=None):
        """
        Move binaries and required configs to assigned location.

        @param ssl str:  this tells the firewall to allow port 443 as well as 80 and 22 to support ssl.
        @param start bool: after installing the service this option is true will add the service to the default proccess manager an strart it .
        @param dns str: default address to run caddy on.
        @param reset bool:  if True this will install even if the service is already installed.
        """
        if self.doneGet('install') and reset is False and self.isInstalled():
           return

        self.cuisine.core.file_copy('{builddir}/caddy_linux_amd64'.format(builddir=self.builddir), '$BINDIR/caddy')
        self.cuisine.bash.profileDefault.addPath(self.cuisine.core.dir_paths['BINDIR'])
        self.cuisine.bash.profileDefault.save()

        addr = dns if ssl and dns else ':80'
        if wwwrootdir is None:
            wwwrootdir = "$JSCFGDIR/cfg/caddy/www"
        C = """
        $addr
        gzip
        log $LOGDIR/caddy/log/access.log
        errors {
            log $LOGDIR/caddy/log/errors.log
        }
        root $WWWROOTDIR
        """.replace("$WWWROOTDIR", wwwrootdir)

        C = C.replace("$addr", addr)
        C = self.replace(C)
        cpath = self.replace("$TEMPLATEDIR/cfg/caddy/caddyfile.conf")
        self.cuisine.core.dir_ensure("$LOGDIR/caddy")
        self.cuisine.core.dir_ensure("$LOGDIR/caddy/log/")
        self.cuisine.core.dir_ensure(wwwrootdir)
        self.cuisine.core.file_write(cpath, C)

        self.doneSet('install')

        if start:
            self.start(ssl)

    def start(self, ssl):
        cpath = self.replace("$JSCFGDIR/caddy/caddyfile.conf")
        self.cuisine.core.file_copy("$TEMPLATEDIR/cfg/caddy", "$JSCFGDIR/caddy", recursive=True)

        # adjust confguration file
        conf = self.cuisine.core.file_read(cpath)
        conf.replace("$TEMPLATEDIR/cfg", "$JSCFGDIR")
        conf = self.replace(conf)
        self.cuisine.core.file_write("$JSCFGDIR/caddy/caddyfile.conf", conf, replaceArgs=True)

        self.cuisine.processmanager.stop("caddy")  # will also kill

        fw = not self.cuisine.core.run("ufw status 2> /dev/null", die=False)[0]

        if ssl:
            # Do if not  "ufw status 2> /dev/null" didn't run properly
            if fw:
                self.cuisine.systemservices.ufw.allowIncoming(443)
                self.cuisine.systemservices.ufw.allowIncoming(80)
                self.cuisine.systemservices.ufw.allowIncoming(22)

            if self.cuisine.process.tcpport_check(80, "") or self.cuisine.process.tcpport_check(443, ""):
                raise RuntimeError("port 80 or 443 are occupied, cannot install caddy")

        else:
            if self.cuisine.process.tcpport_check(80, ""):
                raise RuntimeError("port 80 is occupied, cannot install caddy")

            PORTS = ":80"
            if fw:
                self.cuisine.systemservices.ufw.allowIncoming(80)
                self.cuisine.systemservices.ufw.allowIncoming(22)

        cmd = self.cuisine.bash.cmdGetPath("caddy")
        self.cuisine.processmanager.ensure("caddy", '%s -conf=%s -email=info@greenitglobe.com' % (cmd, cpath))

    def stop(self):
        self.cuisine.processmanager.stop("caddy")

    def caddyConfig(self, sectionname, config):
        """
        config format see https://caddyserver.com/docs/caddyfile
        """
        raise RuntimeError("needs to be implemented")
