# ays run show

```shell
Usage: ays run show [OPTIONS]

  show detail of a run.

  If the --key option is not set, show the detail of the last run. if --logs
  option is set, also show the logs of each job. If -f option is set, the
  command will print the status of the run until it succeed.

Options:
  -k, --key TEXT  key of the run to show
  -l, --logs      show logs of the jobs
  -f, --follow    follow run execution
  --help          Show this message and exit.
```

```toml
!!!
title = "AYS Run Show"
tags= ["ays"]
date = "2017-03-02"
categories= ["ays_cmd"]
```
