# Deplying owncloud using AYS
First we should define our Blueprint like this

## blueprints/oc.yaml
```
sshkey__demo:

g8client__env1:
    url: 'be-g8-1.demo.greenitglobe.com'
    login: 'login'
    password: 'password'
    account: 'account'

vdc__myspaceboc3:
    g8client: 'env1'
    location: 'be-g8-1'

blueowncloud__oc2:
    hostprefix: 'boc3'
    vdc: myspaceboc3
    datadisks:
      - 1000
      - 1000
```

1- create `sshkey` service to be used through our services.
2- create `g8client` connection service named `env1`.
3- create `vdc` named `myspaceboc3`.
4- create `blueowncloud` service named `oc2` with its required parameters.
> blueowncloud is a service that configures a certain setup for owncloud
`docker that hosts tidb` as the backend, `docker for php and nginx and owncloud application` and `docker that hosts caddy to work as a reverse proxy`

```
!!!
title = "Deplying owncloud using AYS"
date = "2017-04-08"
tags = []
```
