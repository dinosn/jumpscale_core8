# Cuisine

Cuisine makes it easy to automate server installations and create configuration recipes by wrapping common administrative tasks, such as installing packages and creating users and groups, in Python functions.

To use cuisine you first need to get an executor that can be local or remote.

To get local a executor:
```
executor = j.tools.executor.getLocal()
cuisine = j.tools.cuisine.get(executor)
```

Or to get a remote executor:
```
executor = j.tools.executor.getSSHBased(addr, port, login, passwd)
cuisine = j.tools.cuisine.get(executor)
```


## Examples

- Print the environment variables of a remote machine:
  ```
  executor = j.tools.executor.getSSHBased(addr, port, login, passwd)
  cuisine = j.tools.cuisine.get(executor)
  print (cuisine.bash.envment)
  ```

- Install MongoDB:
  ```
  cuisine.apps.mongodb.install
  ```

- Copy a file:
  ```
  cuisine.core.file_copy("/opt/code/file1", "/opt/code/file2")
  ```

For more information on Cuisine check the [Cuisine documentation](../Cuisine/Cuisine.md).

```
!!!
title = "Cuisine"
date = "2017-04-08"
tags = []
```
