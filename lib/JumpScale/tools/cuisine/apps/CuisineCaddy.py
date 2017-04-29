from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineCaddy(app):

    NAME = "caddy"
    defaultfeatures = ['http.filemanager', 'http.cors']

    def _init(self):
        self.BUILDDIR_ = self.replace("$BUILDDIR/caddy")
        self.CODEDIR_ = self.replace("$CODEDIR/github/mholt/caddy")

    def reset(self):
        app.reset(self)
        self._init()

    def build(self, ssl=False, start=True, dns=None, reset=False, wwwrootdir=None, install=True, features=defaultfeatures):
        """
        Get/Build the binaries of caddy itself.
        :param features: is used to specify the required features in the installation. Currently the default installation
        will add the following features: filemanager, cors
        """
        if self.doneGet('build') and reset is False:
            return

        features = ",".join(features)
        if self.core.isMac:
            caddy_url = 'https://caddyserver.com/download/darwin/amd64?plugins=%s' % features
            dest = '$TMPDIR/caddy_darwin_amd64_custom.zip'
        else:
            caddy_url = 'https://caddyserver.com/download/linux/amd64?plugins=%s' % features
            dest = '$TMPDIR/caddy_linux_amd64_custom.tar.gz'
        self.cuisine.core.file_download(caddy_url, dest)
        self.cuisine.core.run('cd $TMPDIR && tar xvf %s' % dest)
        if install:
            self.install(ssl, start, dns, reset, wwwrootdir)

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

        self.cuisine.core.file_copy(
            '$TMPDIR/caddy', '$BINDIR/caddy')
        self.cuisine.bash.profileDefault.addPath(self.cuisine.core.dir_paths['BINDIR'])
        self.cuisine.bash.profileDefault.save()
        addr = ':8000'
        if not self.core.isMac:
            addr = dns if ssl and dns else ':80'

        C = """
        $addr
        gzip
        log $LOGDIR/caddy/log/access.log
        errors {
            log $LOGDIR/caddy/log/errors.log
        }
        """

        C = C.replace("$addr", addr)
        C = self.replace(C)
        C = C + "\nroot $WWWROOTDIR".replace("$WWWROOTDIR", wwwrootdir) if wwwrootdir else C
        cpath = self.replace("$TEMPLATEDIR/cfg/caddy/caddyfile.conf")
        self.cuisine.core.dir_ensure("$LOGDIR/caddy")
        self.cuisine.core.dir_ensure("$LOGDIR/caddy/log/")
        if wwwrootdir:
            self.cuisine.core.dir_ensure(wwwrootdir)
        self.cuisine.core.file_write(cpath, C)

        self.doneSet('install')

        if start:
            self.start(ssl)

    def start(self, ssl, agree=True, cfg_path='', email='info@greenitglobe.com'):
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
        if cfg_path:
            cpath = cfg_path
        if agree:
            self.cuisine.processmanager.ensure("caddy", 'ulimit -n 8192; %s -agree -conf=%s -email=%s' % (cmd, cpath, email))
        else:
            self.cuisine.processmanager.ensure("caddy", 'ulimit -n 8192; %s -conf=%s -email=%s' % (cmd, cpath, email))

    def stop(self):
        self.cuisine.processmanager.stop("caddy")

    def caddyConfig(self, sectionname, config):
        """
        config format see https://caddyserver.com/docs/caddyfile
        """
        raise RuntimeError("needs to be implemented")
