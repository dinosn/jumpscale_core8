## NetConfig

```py
j.sal.netconfig
```

### This library enables the user to configure the network by doing the followig:

* Choosing another root to manipulate the config files

```py
j.sal.netconfig.chroot(root)
```

* Configuring a new interface

```py
etconfig.interface_configure(interfaceName, ipaddr=None, bridgeInterface=None, gateway=None, dhcp=False, apply=True)
```

* Finding all interfaces and shut them all down with ifdown with the option of excluding certain interfaces

```py
j.sal.netconfig.interfaces_shutdown(excludes)
    #excludes varibale is a list of excluded interfaces.
```

* Resetting configuration of all interfaces

```py
j.sal.netconfig.interfaces_reset(shutdown)
    #shutdown is a boolean variable which states if you want to shutdown the network.
```

* Delete an interface

```py
j.sal.netconfig.interface_remove(interface, apply)
    #apply is a boolean variable
```

* Change the hostname

```py
j.sal.netconfig.hostname_set(hostname)
```

* Setting of a nameserver

```py
j.sal.netconfig.nameserver_set(addr)
```

* Configuring DHCP on a certain interface

```py
j.sal.netconfig.interface_configure_dhcp(interface, apply)
j.sal.netconfig.interface_configure_dhcp_bridge(interface, bridge_interface, apply)
# apply is a boolean variable which applies settings immediatly by restarting interfaces and services
```

* Restarting interfaces

```py
j.sal.netconfig.interfaces_restart(interface)
# if no interface is provided, all interfaces will be restarted.
```

* Enabling of proxy server

```py
j.sal.netconfig.proxy_enable()
```

* Removing interfaces from a certain network by deleting their IP addresses

```py
j.sal.netconfig.interface_remove_ipaddr(network)
```

Bringing all bridges down and set specified interface with an IP address or on dhcp if no IP address, is provided

```py
j.sal.netconfig.interface_configure_dhcp_waitdown(interface, ipaddr, gateway, mask, config)
# config is a boolean variable that if set True then will store in linux configuration files
```

@todo