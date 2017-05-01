# ays actor update

```shell
ays actor update --help
Usage: ays actor update [OPTIONS]

  Update actor to a new version. Any change detected in the actor will be
  propagated to the services and processChange method will be called all the
  way from actor to service instances.

  if the `--reschedule` option is given, all the action that were in `error` state will remain in `error` state after the update
  instead of beeing switched to state `changed`

Options:
  -n, --name TEXT  name of the actor to update
  -r, --reschedule  reschedule actions in error state after update
  --help           Show this message and exit.
```

Example usage:
`ays actor update -n node.ovc`

```toml
!!!
title = "AYS Actor Update"
tags= ["ays"]
date = "2017-03-02"
categories= ["ays_cmd"]
```
