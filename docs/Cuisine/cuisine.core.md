## cuisine.core

The `cuisine.core` module handles basic file system operations and command execution.

Examples for methods in `core`:

- **command_check**: tests if the given command is available on the system
- **Command_ensure**: ensures that the given command is present, if not installs the package with the given name, which is the same as the command by default
- **createDir**: to create a directory
- **execute_python**: execute a Python script (script as content) in a remote tmux command, the stdout will be returned
- **execute_jumpscript**: execute a JumpScript (script as content) in a remote tmux command, the stdout will be returned
- **file_append**: appends the given content to the remote file at the given location
- **file_read**: read the content of a file.* file_copy: copy a file
- **file_write**: write the content to a file
- **isArch**, **isDocker**, **isMac**, **isLxc**, **isUbuntu**: check for the target os
- **run**: run a command

  ```py
  cuisine.run('ls')
  cuisine.run('false', die=False) //it won't raise an error
  ```

- **run_script**: run a script
  
  ```py
  cuisine.run_script('cd /\npwd')
  ```

- **sudo**: run a command using sudo

  ```py
  cuisine.sudo('apt-get  install httpie')
  ```

- **args_replace**: replace arguments inside commands and paths such as `$binDir`, `$hostname`, `$codeDir`, `$tmpDir`
  
  ```py
  cuisine.arg_replace('$binDir/python -c "print(1)"')
  ```