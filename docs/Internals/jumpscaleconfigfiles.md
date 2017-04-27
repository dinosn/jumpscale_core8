# Jumpscale Config Files

Are in YAML format In this section we list the known config files (there should be no others). All other configurations are done in AYS yaml files

all config files are stored in /optvar/cfg/Jumpscale

## ays.yaml

```yaml
production: False
oauth:
   jwt_key: "-----BEGIN PUBLIC KEY-----\nMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n2\n7MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny6\n6+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv\n-----END PUBLIC KEY-----\n"
   client_secret: "clientsecret"
   redirect_uri: "http://172.17.0.5:8200/api/oauth/callback"
   client_id: "clientid"
   organization: "orgid"

```

## system.yaml

```yaml
dirs:
  BASEDIR: /opt
  BINDIR: /opt/jumpscale8/bin
  BUILDDIR: /optvar/build
  CFGDIR: /optvar/cfg
  CODEDIR: /opt/code
  DATADIR: /optvar/data
  GOPATHDIR: /opt/go/proj/
  GOROOTDIR: /opt/go/root/
  HOMEDIR: /root
  HRDDIR: /optvar/cfg/hrd
  JSAPPSDIR: /opt/jumpscale8/apps
  JSBASEDIR: /opt/jumpscale8
  JSCFGDIR: /optvar/cfg/jumpscale/
  JSLIBDIR: /opt/jumpscale8/lib/JumpScale/
  JSLIBEXTDIR: /opt/jumpscale8/lib/JumpScaleExtra/
  LIBDIR: /opt/lib/
  LOGDIR: /optvar/log
  NIMDIR: /opt/nim/
  PIDDIR: /optvar/cfg/pid
  STARTDIR: /root
  TEMPLATEDIR: /opt/templates
  TMPDIR: /tmp
  VARDIR: /optvar
identity:
  EMAIL: ''
  FULLNAME: ''
  GITHUBUSER: ''
system:
  AYSBRANCH: 8.2.0
  DEBUG: false
  JSBRANCH: 8.2.0
  SANDBOX: false

```

if system.logging = 0 then there will no no logs send to redis or any other log target

## logging.yaml
```yaml

mode: 'DEV'
level: 'DEBUG'

filter:
    - 'j.sal.fs'
    - 'j.data.hrd'
    - 'j.application'

```
## whoami.hrd

```
email                   =
fullname                =
git.login               =
git.passwd              =
```

## system redis

```
redis.addr =
redis.port =
redis.passwd =
```

can all be left empty, or file does not have to exist

## realitydb

```
realitydb.addr =
realitydb.port =
realitydb.login =
realitydb.passwd =
```

can all be left empty, or file does not have to exist

## statsdb

```
statsdb.addr =
statsdb.port =
statsdb.login =
statsdb.passwd =
statsdb.interval = 60
```

interval is every how many sec aggregation is being done

can all be left empty, or file does not have to exist

```
!!!
title = "Jumpscaleconfigfiles"
date = "2017-04-08"
tags = []
```
