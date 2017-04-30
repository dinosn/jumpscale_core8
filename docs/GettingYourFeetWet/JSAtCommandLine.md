# JumpScale At The Command Line

JumpScale offers the following command line tools:

 * [ays](##ays)
 * [jsdocker](##jsdocker)
 * [jscode](##jscode)
 * [jsdesktop](##jsdesktop)
 * [jsnode](##jsnode)


## ays
Wrapper to JumpScale's **At Your Service** tool.

```
Usage: ays [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  action     Shortcut to execute actions blocks this...
  actor      Group of commands about actors
  blueprint  will process the blueprint(s) pointed by name...
  reload     Reload AYS objects in memory
  repo       Group of commands about AYS repositories
  run        Group of commands about runs
  service    Group of commands about services
  start      start an ays service in tmux
  template   Group of commands about actor templates

```

## jsdocker
Wrapper to Docker to do Docker operations.

```bash
Usage: jsdocker [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  commit
  create
  destroy
  destroyall
  execute
  exporttgz
  getip
  importrsync
  list
  pull
  push
  resetdocker
  restart
  start
  stop
```

## jscode
Wrapper to Git to do operations on multiple repositories.

```
Usage: jscode [OPTIONS] ACTION

Options:
  -n, --name TEXT           name or partial name of repo, can also be comma
                            separated, if not specified then will ask, if '*'
                            then all.
  --url TEXT                url
  -m, --message TEXT        commit message
  -b, --branch TEXT         branch
  -a, --accounts TEXT       comma separated list of accounts, if not specified
                            then will ask, if '*' then all.
  -u, --update TEXT         update merge before doing push or commit
  -f, --force TEXT          auto answer yes on every question
  -d, --deletechanges TEXT  will delete all changes when doing update
  -o, --onlychanges TEXT    will only do an action where modified files are
                            found
  --help                    Show this message and exit.

Actions:
  get
  commit
  push
  update
  status
  list
  init
  ```

## jsdesktop
Wrapper to Remote Desktop Protocol (RDP).

```
usage: jsdesktop [OPTIONS] COMMAND

Options:
  -n, --name NAME             desktop nr or name
  -d, --desktop               opendesktop
  -p, --passwd PASSWD         password for desktop

  --help                      Show this help message and exit

Commands:
  ps
  new
  list
  killall
  delete
  configure
  rdp
  userconfig
```

## jsnode
Wrapper to list and manage nodes in a G8 grid.

```
usage: jsnode [OPTIONS] COMMAND

Options:
  -h, --help                   Show this help message and exit
  -nid, --nodeid NID       Ex: -nid=1(note the = sign)
  -gid, --gridid GID       Filter on grid used for list
  --roles ROLES            Used with addrole or deleterole. ex: --roles=node,computenode.kvm(note the = sign). List is comma seperated

  --help                      Show this help message and exit

Commands:
  delete
  list
  enable
  disable
  addrole
  deleterole
```

```
!!!
title = "JSAtCommandLine"
date = "2017-04-08"
tags = []
```

```
!!!
title = "JSAtCommandLine"
date = "2017-04-08"
tags = []
```

```
!!!
title = "JSAtCommandLine"
date = "2017-04-08"
tags = []
```
