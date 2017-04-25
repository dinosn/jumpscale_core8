#!/usr/bin/env bash
set -ex

export STARTDIR=$PWD

if [ -d "/tmp" ]; then
    export TMPDIR="/tmp"
fi

cd $TMPDIR

#TO RESET, to develop faster uncomment
rm -f $TMPDIR/done.yaml
rm -rf /opt/var/cfg/jumpscale/
rm -rf /optvar/cfg/jumpscale/
rm -f $TMPDIR/jumpscale_done.yaml
rm -rf $TMPDIR/jsexecutor.json
rm -f $TMPDIR/done
mkdir -p /root/.ssh

cd $TMPDIR
function clean_system {
    set +ex
    sed -i.bak /AYS_/d $HOME/.bashrc
    sed -i.bak /JSDOCKER_/d $HOME/.bashrc
    sed -i.bak /'            '/d $HOME/.bashrc
    set -ex
}

function osx_install {
    set +ex
    brew unlink curl
    brew unlink python3
    brew unlink git
    set -ex
    brew install python3
    brew link --overwrite python3
    brew install git
    brew link --overwrite git
    brew install curl
    brew link --overwrite curl
    brew install snappy
    sudo mkdir -p /optvar
    sudo chown -R $USER /optvar
    sudo mkdir -p /opt
    sudo chown -R $USER /opt
}

function alpine_install {
    apk add git
    apk add curl
    apk add wget
    apk add python3
    apk add python3-dev
    apk add gcc
    apk add make
    apk add alpine-sdk
    apk add snappy-dev
    apk add py3-cffi
    apk add libffi
    apk add libffi-dev
    apk add openssl-dev
    apk add libexecinfo-dev
    apk add linux-headers
    apk add redis
    apk add tmux
}

function pip_install {
    cd $TMPDIR
    rm -rf get-pip.py
    curl -k https://bootstrap.pypa.io/get-pip.py > get-pip.py;python3 get-pip.py
    pip3 install --upgrade pip setuptools
    pip3 install --upgrade pyyaml
    # pip3 install --upgrade uvloop
    pip3 install --upgrade ipython
    pip3 install --upgrade python-snappy
    pip3 install --upgrade colorlog
}

if [ "$(uname)" == "Darwin" ]; then
    # Do something under Mac OS X platform
    # echo 'install brew'
    export LANG=C; export LC_ALL=C
    osx_install

elif [ -e /etc/alpine-release ]; then
    alpine_install

elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # export LC_ALL='C.UTF-8'
    locale-gen en_US.UTF-8
    export LANG=en_US.UTF-8
    export LC_ALL=en_US.UTF-8
    dist=`grep DISTRIB_ID /etc/*-release | awk -F '=' '{print $2}'`
    if [ "$dist" == "Ubuntu" ]; then
        echo "found ubuntu"
        apt-get install mc curl git ssh python3.5 -y
        apt-get install python3-pip -y
        apt-get install libssl-dev -y
        apt-get install python3-dev -y
        apt-get install build-essential -y
        apt-get install libffi-dev -y
        apt-get install libsnappy-dev libsnappy1v5 -y
        rm -f /usr/bin/python
        rm -f /usr/bin/python3
        ln -s /usr/bin/python3.5 /usr/bin/python
        ln -s /usr/bin/python3.5 /usr/bin/python3

        ssh-keyscan github.com >> /root/.ssh/known_hosts
    fi

elif [ "$(expr substr $(uname -s) 1 9)" == "CYGWIN_NT" ]; then
    # Do something under Windows NT platform
    export LANG=C; export LC_ALL=C
    lynx -source rawgit.com/transcode-open/apt-cyg/master/apt-cyg > apt-cyg
    install apt-cyg /bin
    apt-cyg install curl
    apt-cyg install python3-dev
    apt-cyg install build-essential
    apt-cyg install openssl-devel
    apt-cyg install libffi-dev
    apt-cyg install python3
    apt-cyg install make
    apt-cyg install unzip
    apt-cyg install git

    ln -sf /usr/bin/python3 /usr/bin/python

    # #install redis
    # cd $TMPDIR
    # rm -rf Redis
    # mkdir Redis
    # cd Redis
    # wget -O Redis-x64-3.2.100.zip https://github.com/MSOpenTech/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.zip
    # unzip Redis-x64-3.2.100.zip
    # chmod +x redis-server.exe
    # cp -f  redis-server.exe /usr/local/bin

fi

clean_system

pip_install

set -ex

cd $STARTDIR

#need to remove, if you want to develop you need to call the install from the code directory
rm -f $TMPDIR/bootstrap.py
rm -f $TMPDIR/InstallTools.py
rm -f $TMPDIR/dependencies.py

if [ -e "bootstrap.py" ]; then
    cp  -f bootstrap.py $TMPDIR/bootstrap.py
    cp  -f InstallTools.py $TMPDIR/InstallTools.py
    cp  -f dependencies.py $TMPDIR/dependencies.py
else
    curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/$JSBRANCH/install/bootstrap.py?$RANDOM  > $TMPDIR/bootstrap.py
    curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/$JSBRANCH/install/InstallTools.py?$RANDOM > $TMPDIR/InstallTools.py
    curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/$JSBRANCH/install/dependencies.py?$RANDOM > $TMPDIR/dependencies.py
fi


cd $TMPDIR
python3 bootstrap.py

cd $STARTDIR
