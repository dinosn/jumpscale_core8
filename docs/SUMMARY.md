
# Summary

* [Introduction](README.md)

  - [Why Using JumpScale](Introduction/WhyJumpScale.md)
  - [Solutions Built with JumpScale](Introduction/JumpScaleSolutions.md)

* [Installation](Installation/Installation.md)
  - [Installation of the JumpScale Sandbox](Installation/JS8.md)
  - [Installation for Development Purposes](Installation/JSDevelopment.md)
  - [More Details about the Installation Process](Installation/JSInstaller.md)
  - [Installing the JumpScale Docker Container](Installation/JSDocker.md)

* [Getting Your Feet Wet](GettingYourFeetWet/GettingYourFeetWet.md)
  - [Ways to Use JumpScale](GettingYourFeetWet/WaysToUseJS.md)
    - [JumpScale Interactive Shell](GettingYourFeetWet/JShell.md)
    - [JumpScale at the Command Line](GettingYourFeetWet/JSAtCommandLine.md)
  - [JumpScale Core Components](GettingYourFeetWet/Components.md)
    - [Various Tools](GettingYourFeetWet/Tools.md)
    - [System Abstraction Layers](GettingYourFeetWet/SALs.md)
    - [Cuisine](GettingYourFeetWet/Cuisine.md)
    - [AYS](GettingYourFeetWet/AYS.md)

* [How To](Howto/Howto.md)
  - [Use Git](Howto/how_to_use_git.md)
    - [Automated](Howto/how_to_use_git_automated.md)
    - [Manually](Howto/how_to_use_git_manually.md)
  - [How to work with SSH](Howto/SSH/SSH.md)
    - [SSH Basics](Howto/SSH/SSHBasics.md)
    - [SSH Agent Tips](Howto/SSH/SSHKeysAgent.md)
  - [Create a Tool for j](Howto/how_to_create_a_tool_for_j.md)
  - [Use the OpenvCloud APIs](Howto/how_to_use_OVC_API.md)
  - [Use the Shell & Debug](Howto/how_to_use_the_shell_and_debug.md)
  - [Add a New SAL](Howto/how_to_add_a_new_SAL.md)

* [Internals](Internals/Internals.md)
  - [Redis](Internals/Redis.md)
  - [Logging](Internals/Logging.md)
  - [JumpScale Config Files](Internals/jumpscaleconfigfiles.md)

* [SALs](SAL/SAL.md)
  - [DiskLayout](SAL/Disklayout.md)
  - [FS](SAL/FS.md)
  - [KVM](SAL/KVM.md)
  - [Open vSwitch](SAL/OpenVSwitch.md)
  - [Samba](SAL/Samba.md)
  - [SSHD](SAL/SSHD.md)
  - [Tmux](SAL/Tmux.md)
  - [Ubuntu](SAL/Ubuntu.md)
  - [UFW](SAL/UFW.md)

* [Cuisine](Cuisine/Cuisine.md)
  - [cuisine.apps](Cuisine/cuisine.apps.md)
  - [cuisine.bash](Cuisine/cuisine.bash.md)
  - [cuisine.btrfs](Cuisine/cuisine.btrfs.md)
  - [cuisine.core](Cuisine/cuisine.core.md)
  - [cuisine.development](Cuisine/cuisine.development.md)
  - [cuisine.group](Cuisine/cuisine.group.md)
  - [cuisine.kwm](Cuisine/cuisine.kvm.md)
  - [cuisine.net](Cuisine/cuisine.net.md)
  - [cuisine.package](Cuisine/cuisine.package.md)
  - [cuisine.processmanager](Cuisine/cuisine.processmanager.md)
  - [cuisine.ssh](Cuisine/cuisine.ssh.md)
  - [cuisine.systemservices](Cuisine/cuisine.systemservices.md)
  - [cuisine.tmux](Cuisine/cuisine.tmux.md)

* [AYS](AYS/AYS-Introduction.md)
  - [Definitions](AYS/Definitions/0-Definitions.md)
    - [AYS Repositories](AYS/Definitions/1-Repositories.md)
    - [AYS Templates, Recipes & Instances](AYS/Definitions/2-Templates-Recipes-Instances.md)
    - [AYS Service Name, Role & Version](AYS/Definitions/3-Name-Role-Version.md)
    - [AYS Service Unique Key](AYS/Definitions/4-Unique-Key.md)
    - [AYS Producers & Consumers](AYS/Definitions/5-Producers-Consumers.md)
    - [AYS Parents & Children](AYS/Definitions/6-Parents-Children.md)
    - [AYS Service Actions](AYS/Definitions/7-Actions.md)
    - [AYS Blueprints](AYS/Definitions/8-Blueprints.md)
  - [What's new in AYS v8.1](AYS/whatsnew.md)
  - [Life Cycle of an AYS Service](AYS/Service-Lifecycle.md)
  - [Commands](AYS/Commands/commands.md)
    - [create_repo](AYS/Commands/create_repo.md)
    - [blueprint](AYS/Commands/blueprint.md)
    - [commit](AYS/Commands/commit.md)
    - [run](AYS/Commands/run.md)
    - [simulate](AYS/Commands/simulate.md)
    - [destroy](AYS/Commands/destroy.md)
    - [delete](AYS/Commands/delete.md)
    - [discover](AYS/Commands/discover.md)
    - [restore](AYS/Commands/restore.md)
    - [run_info](AYS/Commands/run_info.md)
    - [do](AYS/Commands/do.md)
    - [list](AYS/Commands/list.md)
    - [repo_list](AYS/Commands/repo_list.md)
    - [update](AYS/Commands/update.md)
    - [test](AYS/Commands/test.md)
    - [show](AYS/Commands/show.md)
    - [state](AYS/Commands/state.md)
    - [set_state](AYS/Commands/set_state.md)
  - [File Locations & Details](AYS/FileDetails/FilesDetails.md)
    - [AYS Template Repo](AYS/FileDetails/AYS-template-repo.md)
    - [AYS Repo](AYS/FileDetails/AYS-repo.md)
    - [service.hrd](AYS/FileDetails/service.hrd.md)
    - [Parent/Child](AYS/FileDetails/Parent-Child.md)
    - [HRD Configuration Files](AYS/FileDetails/HRD.md)
  - [AYS File System](AYS/G8OS-FS.md)
  - [AYS Portal](AYS/AYS-Portal.md)
  - [Building an AYS Service](AYS/Building.md)
  - [AYS Examples](AYS/Examples/Home.md)
    - [Automate the Creation Docker Containers](AYS/Examples/DockerExample.md)
    - [Automate the Creation of 2 Virtual Machines in OpenvCloud](AYS/Examples/OVCExample.md)

* [Agent & Agent Controller]
  - [Agent Configuration](AgentController8/AgentConfiguration.md)
  - [Controller8](AgentController8/AgentController8.md)
  - [Command Syntax](AgentController8/Command-Syntax.md)
  - [Configurations](AgentController8/Configuration.md)
  - [Controller Configuration](AgentController8/ControllerConfiguration.md)
  - [EasyClient](AgentController8/EasyClient.md)
  - [Install](AgentController8/Install.md)
  - [Internals](AgentController8/Internals.md)
  - [JumpScripts](AgentController8/Jumpscripts.md)
  - [LogLevels](AgentController8/LogLevels.md)
  - [Manual Installation](AgentController8/ManualInstall.md)
  - [MS1 Driver](AgentController8/MS1driver.md)
  - [Port forwarding](AgentController8/Port-forwarding.md)
  - [Python Client](AgentController8/PythonClient.md)
  - [Scripts Distribution](AgentController8/ScriptsDistribution.md)
  - [Security](AgentController8/Security.md)
  - [Stats](AgentController8/Stats.md)
  - [Tutorial](AgentController8/Tutorial.md)

* [Walkthroughs](Walkthrough/Walkthrough.md)
  - [Working with Docker using the Docker SAL](Walkthrough/SAL/Docker.md)
  - [Installing Caddy using Cuisine](Walkthrough/Cuisine/install_caddy_on_docker.md)
  - [Installing Docker and Caddy with AYS](Walkthrough/AYS/Install_docker_and_caddy.md)

* [JumpScale API](JumpscaleAPI/SUMMARY.md)
