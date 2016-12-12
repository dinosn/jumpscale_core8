from JumpScale import j
import os
import textwrap
from time import sleep


app = j.tools.cuisine._getBaseAppClass()


class CuisineNGINX(app):
    NAME = 'nginx'

    def __init__(self, executor, cuisine):
        self._executor = executor
        self._cuisine = cuisine

    def _build(self):
        # TODO: *3 optional
        # build nginx
        return True

    def get_basic_nginx_conf(self):
        return """\
        user www-data;
        worker_processes auto;
        pid /run/nginx.pid;

        events {
        	worker_connections 768;
        	# multi_accept on;
        }

        http {

        	##
        	# Basic Settings
        	##

        	sendfile on;
        	tcp_nopush on;
        	tcp_nodelay on;
        	keepalive_timeout 65;
        	types_hash_max_size 2048;
        	# server_tokens off;

        	# server_names_hash_bucket_size 64;
        	# server_name_in_redirect off;

        	include $JSAPPDIR/nginx/etc/mime.types;
        	default_type application/octet-stream;

        	##
        	# SSL Settings
        	##

        	ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
        	ssl_prefer_server_ciphers on;

        	##
        	# Logging Settings
        	##

        	access_log /var/log/nginx/access.log;
        	error_log /var/log/nginx/error.log;

        	##
        	# Gzip Settings
        	##

        	gzip on;
        	gzip_disable "msie6";

        	##
        	# Virtual Host Configs
        	##

        	include $JSAPPDIR/nginx/etc/conf.d/*;
        	include $JSAPPDIR/nginx/etc/sites-enabled/*;
        }
        """

    def install(self, start=True):
        """
        can install through ubuntu

        """
        # Install through ubuntu
        self._cuisine.package.mdupdate()
        self._cuisine.package.ensure('nginx')
        # link nginx to binDir and use it from there

        # self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/")
        # self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/bin")
        # self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/etc")
        self._cuisine.core.dir_ensure("$JSCFGDIR")
        self._cuisine.core.dir_ensure("$TMPDIR")
        self._cuisine.core.dir_ensure("/optvar/tmp")
        self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/")
        self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/bin")
        self._cuisine.core.dir_ensure("$JSAPPDIR/nginx/etc")
        self._cuisine.core.dir_ensure("$JSCFGDIR/nginx/etc")

        self._cuisine.core.file_copy('/usr/sbin/nginx', '$JSAPPDIR/nginx/bin/nginx', overwrite=True)
        self._cuisine.core.dir_ensure('/var/log/nginx')
        self._cuisine.core.file_copy('/etc/nginx/*', '$JSAPPDIR/nginx/etc/', recursive=True)  # default conf
        self._cuisine.core.file_copy('/etc/nginx/*', '$JSCFGDIR/nginx/etc/', recursive=True)  # variable conf
        basicnginxconf = self.get_basic_nginx_conf()
        defaultenabledsitesconf = """\

        server {
            listen 80 default_server;
            listen [::]:80 default_server;



            root /var/www/html;

            # Add index.php to the list if you are using PHP
            index index.html index.htm index.nginx-debian.html index.php;

            server_name _;

            location / {
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                try_files $uri $uri/ =404;
            }

            # pass the PHP scripts to FastCGI server listening on 127.0.0.1:9000

            location ~ \.php$ {
                include $JSAPPDIR/nginx/etc/snippets/fastcgi-php.conf;

            #   # With php7.0-cgi alone:
                fastcgi_pass 127.0.0.1:9000;
                # With php7.0-fpm:
                # fastcgi_pass unix:/run/php/php7.0-fpm.sock;
            }

            # deny access to .htaccess files, if Apache's document root
            # concurs with nginx's one
            #
            #location ~ /\.ht {
            #   deny all;
            #}
        }

        """
        basicnginxconf = textwrap.dedent(basicnginxconf)
        basicoptvarnginxconf = basicnginxconf.replace("$JSAPPDIR", "$JSCFGDIR")
        basicnginxconf = self._cuisine.core.args_replace(basicnginxconf)
        basicoptvarnginxconf = self._cuisine.core.args_replace(basicoptvarnginxconf)

        defaultenabledsitesconf = textwrap.dedent(defaultenabledsitesconf)
        defaultenabledsitesconf = self._cuisine.core.args_replace(defaultenabledsitesconf)

        self._cuisine.core.file_write("$JSAPPDIR/nginx/etc/nginx.conf", content=basicnginxconf)
        self._cuisine.core.file_write("$JSCFGDIR/nginx/etc/nginx.conf", content=basicoptvarnginxconf)
        self._cuisine.core.file_write("$JSAPPDIR/nginx/etc/sites-enabled/default", content=defaultenabledsitesconf)
        fst_cgi_conf = self._cuisine.core.file_read("$JSAPPDIR/nginx/etc/fastcgi.conf")
        fst_cgi_conf = fst_cgi_conf.replace("include fastcgi.conf;", "include /opt/jumpscale8/apps/nginx/etc/fastcgi.conf;")
        self._cuisine.core.file_write("$JSAPPDIR/nginx/etc/fastcgi.conf", content=fst_cgi_conf)

        #self._cuisine.core.file_link(source="$JSCFGDIR/nginx", destination="$JSAPPDIR/nginx")
        if start:
            self.start()

    def build(self, install=True, start=True):
        self._build()
        if install:
            self.install(start)

    def start(self, name="nginx", nodaemon=True, nginxconfpath=None):
        nginxbinpath = '$JSAPPDIR/nginx/bin'
        if nginxconfpath is None:
            nginxconfpath = '$JSCFGDIR/nginx/etc/nginx.conf'
        nginxconfpath = self._cuisine.core.args_replace(nginxconfpath)
        nginxconfpath = os.path.normpath(nginxconfpath)
        if self._cuisine.core.file_exists(nginxconfpath):
            nginxcmd = "$JSAPPDIR/nginx/bin/nginx -c {nginxconfpath} -g 'daemon off;'".format(nginxconfpath=nginxconfpath)  # foreground
            nginxcmd = self._cuisine.core.args_replace(nginxcmd)
            print("cmd: ", nginxcmd)
            self._cuisine.processmanager.ensure(name=name, cmd=nginxcmd, path=nginxbinpath)
        else:
            raise RuntimeError('failed to start nginx')

    def stop(self):
        self._cuisine.processmanager.stop("nginx")

    def test(self):
        # host a file test can be reached
        raise NotImplementedError
