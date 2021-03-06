# AYS Template Repo

AYS actor template repositories contain all the metadata defining the lifecycle of a service, from pre-installation to monitoring.

An example is [ays_jumpscale8](https://github.com/Jumpscale/ays_jumpscale8), defining the full life cycle of all JumpScale services.

You can configure which AYS template repositories to use in a configuration file:

- Edit the file `/optvar/hrd/system/atyourservice.hrd`
- Add a new section for every metadata repository you want to add:

```shell
metadata.jumpscale             =
    branch:'master',
    url:'https://github.com/Jumpscale/ays_jumpscale8',

metadata.openvcloud        =
    branch: 'master',
    url:'https://git.aydo.com/0-complexity/openvcloud_ays',
```

All metadata repositories are cloned as subdirectories of `/opt/code/$type/`:

- Repositories from GitHub are cloned into `/opt/code/github`

  - So `https://github.com/Jumpscale/ays_jumpscale8` is cloned into `/opt/code/github/jumpscale/ays_jumpscale8`

- Repositories from other Git systems are cloned into `/opt/code/git/`

Each AYS actor template has following files:

- **schema.hrd**

  - Which is the schema for the service instance metadata file (`instance.hrd`) relevant for an instance of the service
  - Contains information about how services interact with each other through:

    - Parenting, for more details see the section [Parents & Children](Definitions/Parents-Children.md)
    - Consumption, for more details see the section [Producers & Consumers](Definitions/Products-Consumers.md)

  - Has parameter definitions used to configure the service

  - Example:

    ```
    image = type:str default:'ubuntu'
    build = type:bool default:False
    build.url = type:str
    build.path = type:str default:''
    ports = type:str list

    sshkey = descr:'authorized sshkey' consume:sshkey:1:1 auto

    os = type:str parent:'os'
    docker = type:str consume:'app_docker':1 auto
    docker.local = type:bool default:False
    ```

- **actor.hrd** (optional)

  - Containing information about recurring action methods, and action triggered by events.

  - Example:
    ```
    recurring.monitor =
        period: 30s,
        log: True,

    recurring.cleanup =
        period: 30s,
        log: False,

    event.telegram.install =
        log:'True',
    event.telegram.update  =
        log:'False',
      ```

- **actions.py** defines the behavior of the service (optional)
