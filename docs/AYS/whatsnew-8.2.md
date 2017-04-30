# What's new in AYS v8.2?
- No more HRD: HRD format has been completly removed from AYS.
It has been replaced by yaml for actor template Configuration and capnp for schema definition.
- In this version we have merge the AYS daemon and API together. Which means you only have one running process that serve everything.


## AsyncIO
We have replaced to usage of Multiprocessing with asyncio.


## Upgrading your templates from 8.1 to 8.2
you can use `j.atyourservice._upgradeTemplate2yaml` tool to upgrade templates from the old hrd version.

```
!!!
title = "Whatsnew 8.2"
date = "2017-04-08"
tags = []
```
