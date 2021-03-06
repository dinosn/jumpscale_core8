from JumpScale import j
import time
import os

base = j.tools.cuisine._getBaseClass()


class CuisineTmux(base):

    def __init__(self, executor, cuisine):
        self._executor = executor
        self._cuisine = cuisine

    def createSession(self, sessionname, screens, user=None, killifexists=True, returnifexists=True):
        """
        @param name is name of session
        @screens is list with nr of screens required in session and their names (is [$screenname,...])
        """
        # if 'ubuntu' in j.core.platformtype.myplatform.platformtypes:
        if not self._cuisine.core.command_check("tmux"):
            self._cuisine.package.install("tmux")
        # else:
        #     from IPython import embed
        #     print("DEBUG NOW sdsd")
        #     embed()
        #     raise RuntimeError("stop debug here")
        #     raise j.exceptions.RuntimeError(message="only support ubuntu", level=1, source="", tags="", msgpub="")
        if returnifexists:
            return
        if killifexists:
            self.killSession(sessionname)

        if len(screens) < 1:
            raise j.exceptions.RuntimeError(
                "Cannot create screens, need at least 1 screen specified")

        env = os.environ.copy()
        env.pop('TMUX', None)
        cmd = "tmux new-session -d -s %s -n %s" % (sessionname, screens[0])
        if user is not None:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        # j.sal.process.run(cmd, env=env)  #TODO: does not work in python3
        self._executor.execute(cmd, showout=False)
        # now add the other screens to it
        if len(screens) > 1:
            for screen in screens[1:]:
                cmd = "tmux new-window -t '%s' -n '%s'" % (sessionname, screen)
                if user is not None:
                    cmd = "sudo -u %s -i %s" % (user, cmd)
                self._executor.execute(cmd, showout=False)

    def executeInScreen(self, sessionname, screenname, cmd, wait=10, cwd=None, env=None, user="root",
                        tmuxuser=None, reset=False, replaceArgs=True, resetAfter=False, die=True, async=False):
        """

        execute command in tmux & wait till error or till ok, default 10 sec
        we will wait X seconds as specified in argument wait.

        if async then we will wait 1 second to see if cmd got started succesfully and the exit
        we do this by checking the error code after 1 second

        @param sessionname Name of the tmux session
        @param screenname Name of the window in the session
        @param cmd command to execute
        @param cwd workingdir for command only in new screen see newscr
        @param env environment variables for cmd only in new screen see newscr (dict)
        @param async, if async will fire & forget
        @param resetAfter if True, will remove the tmux session after execution (error or not)

        will return rc,out
        """
        cmdorg = cmd
        env = env or dict()
        envstr = ""
        for name, value in list(env.items()):
            envstr += "export %s=%s\n" % (name, value)

        if replaceArgs:
            cmd = self._cuisine.core.args_replace(cmd)

        # Escape the double quote character in cmd
        cmd = cmd.replace('"', r'\"')

        if reset:
            self.killWindow(sessionname, screenname)

        if cmd.strip() is "":
            raise j.exceptions.Input(message="cmd cannot be empty", level=1, source="", tags="", msgpub="")

        self.createWindow(sessionname, screenname, cmd=cmd, user=tmuxuser)
        pane = self._getPane(sessionname, screenname, user=tmuxuser)
        env = os.environ.copy()
        env.pop('TMUX', None)

        # set environment if not empty
        if envstr != "":
            cmd2 = "tmux send-keys -t '%s' '%s\n'" % (pane, envstr)
            if tmuxuser is not None:
                cmd2 = "sudo -u %s -i %s" % (tmuxuser, cmd2)
            self._executor.executeRaw(cmd2, die=True)

        # if path to go on, set it
        if cwd:
            cwd = "cd %s;" % cwd
            cmd = "%s %s" % (cwd, cmd)

        # catch if error
        cmd = "echo **START**;%s && echo **OK** || echo **ERROR**" % cmd

        if user != "root":
            cmd = "su -c \"%s\" %s" % (cmd, user)

        if cmd.find("$") != -1:
            cmd = cmd.replace("$", "\\$")

        cmd = cmd.strip()

        # now send the string to the session
        cmd2 = "tmux send-keys -t '%s' \"%s\" ENTER" % (pane, cmd)
        if tmuxuser is not None:
            cmd2 = "sudo -u %s -i %s" % (tmuxuser, cmd2)

        rc, out, err = self._executor.executeRaw(cmd2, showout=False, die=False)

        def checkOutput(die, async=False):
            out = ""
            counter = 0
            ffound = False
            while not ffound:
                rc, out, err = self._executor.executeRaw("tmux capture-pane -pS -5000", showout=False)
                # initial command needs to go
                out = out.split('%s\n' % cmd)[-1]
                ffound = '**START**' in out
                if not ffound:
                    time.sleep(0.1)
                    print("reread from tmux, cmd did not start yet")
                counter += 1
                if out.find("**ERROR**") != -1:
                    break
                if counter > 10:
                    break

            out = out.split("**START**")[-1]
            if out.find("**OK**") != -1:
                out = out.split("**OK**")[0]
                out = out.replace("**OK**", "")
                out = out.strip()
                if not out.endswith("\n"):
                    out += "\n"
                return 0, out
            elif j.sal.process.checkProcessRunning(cmd):
                # Warning: It's either hanging or running until explicitly closed
                if not out.endswith("\n"):
                    out += "\n"
                return 0, out
            elif out.find("**ERROR**") != -1:
                out = out.replace("**OK**", "")
                out = out.split("**ERROR**")[-2]
                out = out.replace("**ERROR**", "")
                out = out.strip() + "\n"
                msg = "Could not execute cmd:%s\n" % cmdorg
                msg += "Out/Err:\n%s\n" % out
                if die:
                    raise j.exceptions.RuntimeError(msg)
                else:
                    return 1, msg
            return 999, out

        if rc == 0:
            if async:
                # we want to check to see if command really executed
                time.sleep(1)
                rc, out = checkOutput(die, async=async)
            elif wait == 0:
                rc, out = checkOutput(die)
            else:
                end = j.data.time.getTimeEpoch() + wait + 1
                while j.data.time.getTimeEpoch() < end:
                    rc, out = checkOutput(die)
                    if rc == 999:
                        rc = 0
                    elif rc > 0 or rc == 0:
                        break

        if resetAfter:
            self.killWindow(sessionname, screenname)

        if die and rc > 0:
            raise j.exceptions.RuntimeError(out)

        return rc, out

    def getSessions(self, user=None):
        cmd = 'tmux list-sessions -F "#{session_name}"'
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        rc, out, err = self._executor.execute(cmd, die=False, showout=False)
        if err:
            out = ""
        return [name.strip() for name in out.split()]

    def getPid(self, session, name, user=None):
        cmd = 'tmux list-panes -t "%s" -F "#{pane_pid};#{window_name}" -a' % session
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        rc, out, err = self._executor.execute(cmd, die=False, showout=False)
        if err:
            return None
        for line in out.split():
            pid, windowname = line.split(';')
            if windowname == name:
                return int(pid)
        return None

    def getWindows(self, session, attemps=5, user=None):
        result = dict()

        cmd = 'tmux list-windows -F "#{window_index}:#{window_name}" -t "%s"' % session
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        rc, out, err = self._executor.execute(cmd, die=False, showout=False, checkok=False)
        if err:
            return result
        for line in out.split():
            idx, name = line.split(':', 1)
            result[int(idx)] = name
        return result

    def createWindow(self, session, name, user=None, cmd=None):
        if session not in self.getSessions(user=user):
            return self.createSession(session, [name], user=user, returnifexists=False)
        windows = self.getWindows(session, user=user)
        if name not in list(windows.values()):
            cmd = "tmux new-window -t '%s:' -n '%s'" % (session, name)
            if user:
                cmd = "sudo -u %s -i %s" % (user, cmd)
            time.sleep(0.2)
            self._executor.execute(cmd, showout=False)

    def logWindow(self, session, name, filename, user=None):
        pane = self._getPane(session, name, user=user)
        if pane:
            cmd = "tmux pipe-pane -t '%s' 'cat >> \"%s\"'" % (pane, filename)
            if user:
                cmd = "sudo -u %s -i %s" % (user, cmd)
            self._executor.execute(cmd, showout=False)

    def windowExists(self, session, name, user=None):
        if session in self.getSessions(user=user):
            if name in list(self.getWindows(session, user=user).values()):
                return True
        return False

    def _getPane(self, session, name, user=None):
        windows = self.getWindows(session, user=user)
        remap = dict([(win, idx) for idx, win in list(windows.items())])
        if name not in remap:
            return None
        result = "%s:%s" % (session, remap[name])
        return result

    def killWindow(self, session, name, user=None):
        try:
            pane = self._getPane(session, name, user=user)
        except KeyError:
            return  # window does nt exist
        cmd = "tmux kill-window -t '%s'" % pane
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        self._executor.execute(cmd, die=False, showout=False)

    def killSessions(self, user=None):
        cmd = "tmux kill-server"
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        self._executor.execute(cmd, die=False, showout=False)  # todo checking

    def killSession(self, sessionname, user=None):
        cmd = "tmux kill-session -t '%s'" % sessionname
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        self._executor.execute(cmd, die=False, showout=False)  # todo checking

    def attachSession(self, sessionname, windowname=None, user=None):
        if windowname:
            pane = self._getPane(sessionname, windowname, user=user)
            cmd = "tmux select-window -t '%s'" % pane
            if user:
                cmd = "sudo -u %s -i %s" % (user, cmd)
            self._executor.execute(cmd, die=False)
        cmd = "tmux attach -t %s" % (sessionname)
        if user:
            cmd = "sudo -u %s -i %s" % (user, cmd)
        self._executor.execute(cmd, showout=False)

    def configure(self, restartTmux=False, xonsh=False):
        C = """

        # https://github.com/seebi/tmux-colors-solarized/blob/master/tmuxcolors-256.conf
        set-option -g status-bg colour235 #base02
        set-option -g status-fg colour136 #yellow
        set-option -g status-attr default

        # set window split
        bind-key v split-window -h
        bind-key b split-window

        # default window title colors
        set-window-option -g window-status-fg colour244 #base0
        set-window-option -g window-status-bg default
        #set-window-option -g window-status-attr dim

        # active window title colors
        set-window-option -g window-status-current-fg colour166 #orange
        set-window-option -g window-status-current-bg default
        #set-window-option -g window-status-current-attr bright

        # pane border
        set-option -g pane-border-fg colour235 #base02
        set-option -g pane-active-border-fg colour240 #base01

        # message text
        set-option -g message-bg colour235 #base02
        set-option -g message-fg colour166 #orange

        # pane number display
        set-option -g display-panes-active-colour colour33 #blue
        set-option -g display-panes-colour colour166 #orange
        # clock
        set-window-option -g clock-mode-colour green #green


        set -g status-interval 1
        set -g status-justify centre # center align window list
        set -g status-left-length 20
        set -g status-right-length 140
        set -g status-left '#[fg=green]#H #[fg=black] #[fg=green,bright]#(uname -r | cut -c 1-6)#[default]'
        set -g status-right '#[fg=green,bg=default,bright]#(tmux-mem-cpu-load) #[fg=red,dim,bg=default]#(uptime | cut -f 4-5 -d " " | cut -f 1 -d ",") #[fg=white,bg=default]%a%l:%M:%S %p#[default] #[fg=blue]%Y-%m-%d'

        # C-b is not acceptable -- Vim uses it
        # set-option -g prefix C-a
        bind-key C-a last-window

        # Start numbering at 1
        set -g base-index 1

        # Allows for faster key repetition
        set -s escape-time 0

        # Rather than constraining window size to the maximum size of any client
        # connected to the *session*, constrain window size to the maximum size of any
        # client connected to *that window*. Much more reasonable.
        setw -g aggressive-resize on

        # Allows us to use C-a a <command> to send commands to a TMUX session inside
        # another TMUX session
        # bind-key a send-prefix

        # Activity monitoring
        setw -g monitor-activity on
        set -g visual-activity on

        # Vi copypaste mode
        set-window-option -g mode-keys vi
        bind-key -t vi-copy 'v' begin-selection
        bind-key -t vi-copy 'y' copy-selection

        # hjkl pane traversal
        # bind h select-pane -L
        # bind j select-pane -D
        # bind k select-pane -U
        # bind l select-pane -R

        # set to main-horizontal, 60% height for main pane
        bind m set-window-option main-pane-height 60\; select-layout main-horizontal

        bind-key C command-prompt -p "Name of new window: " "new-window -n '%%'"

        # reload config
        bind r source-file ~/.tmux.conf \; display-message "Config reloaded..."

        # auto window rename
        set-window-option -g automatic-rename

        # color
        set -g default-terminal "screen-256color"

        # status bar
        set-option -g status-utf8 on

        # https://github.com/edkolev/dots/blob/master/tmux.conf
        # Updates for tmux 1.9's current pane splitting paths.

        # from powerline
        run-shell "tmux set-environment -g TMUX_VERSION_MAJOR $(tmux -V | cut -d' ' -f2 | cut -d'.' -f1 | sed 's/[^0-9]*//g')"
        run-shell "tmux set-environment -g TMUX_VERSION_MINOR $(tmux -V | cut -d' ' -f2 | cut -d'.' -f2 | sed 's/[^0-9]*//g')"

        set -g mouse on


        # rm mouse mode fail
        # if-shell '\( #{$TMUX_VERSION_MAJOR} -eq 2 -a #{$TMUX_VERSION_MINOR} -ge 1\) -o #{$TMUX_VERSION_MAJOR} -gt 2' 'set -g mouse off'
        # if-shell '\( #{$TMUX_VERSION_MAJOR} -eq 2 -a #{$TMUX_VERSION_MINOR} -lt 1\) -o #{$TMUX_VERSION_MAJOR} -le 1' 'set -g mode-mouse off'

        # fix pane_current_path on new window and splits
        if-shell "#{$TMUX_VERSION_MAJOR} -gt 1 -o \( #{$TMUX_VERSION_MAJOR} -eq 1 -a #{$TMUX_VERSION_MINOR} -ge 8 \)" 'unbind c; bind c new-window -c "#{pane_current_path}"'
        # if-shell "#{$TMUX_VERSION_MAJOR} -gt 1 -o \( #{$TMUX_VERSION_MAJOR} -eq 1 -a #{$TMUX_VERSION_MINOR} -ge 8 \)" "unbind '"'; bind '"' split-window -v -c '#{pane_current_path}'"
        if-shell "#{$TMUX_VERSION_MAJOR} -gt 1 -o \( #{$TMUX_VERSION_MAJOR} -eq 1 -a #{$TMUX_VERSION_MINOR} -ge 8 \)" 'unbind v; bind v split-window -h -c "#{pane_current_path}"'
        if-shell "#{$TMUX_VERSION_MAJOR} -gt 1 -o \( #{$TMUX_VERSION_MAJOR} -eq 1 -a #{$TMUX_VERSION_MINOR} -ge 8 \)" 'unbind %; bind % split-window -h -c "#{pane_current_path}"'

        """

        if xonsh:
            C += "set -g default-command \"xonsh\"\n\n"

        self._cuisine.core.file_write("$homeDir/.tmux.conf", C)

        if restartTmux:
            self._cuisine.core.run("killall tmux", die=False)

    def __str__(self):
        return "cuisine.tmux:%s:%s" % (getattr(self._executor, 'addr', 'local'), getattr(self._executor, 'port', ''))

    __repr__ = __str__
