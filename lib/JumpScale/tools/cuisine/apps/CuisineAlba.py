from JumpScale import j
from time import sleep


from ActionDecorator import ActionDecorator


"""
please ensure that the start and build methods are separate and
the build doesnt place anyfile outside opt as it will be used in aysfs mounted system
"""


class actionrun(ActionDecorator):

    def __init__(self, *args, **kwargs):
        ActionDecorator.__init__(self, *args, **kwargs)
        self.selfobjCode = "cuisine=j.tools.cuisine.getFromId('$id');selfobj=cuisine.apps.alba"


class Alba:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine
        self.logger = j.logger.get("j.tools.cuisine.alba")
        
        self.ocaml_version = '4.02.3'
        self.opam_root = None

    @actionrun(action=True)
    def build(self, start=True):
        self._install_deps()
        self._build()

    def _install_deps_opam(self):
        self.cuisine.package.update()
        self.cuisine.package.upgrade(distupgrade=True)

        apt_deps = """
        build-essential m4 apt-utils libffi-dev libssl-dev libbz2-dev libgmp3-dev libev-dev libsnappy-dev \
        libxen-dev help2man pkg-config time aspcud wget rsync darcs git unzip protobuf-compiler libgcrypt20-dev \
        libjerasure-dev yasm automake python-dev python-pip debhelper psmisc strace curl g++ libgflags-dev \
        sudo libtool libboost-all-dev fuse sysstat ncurses-dev
        """
        self.cuisine.package.multiInstall(apt_deps, allow_unauthenticated=True)
        
        # opam
        
        self.opam_root = self.cuisine.core.args_replace('$tmpDir/OPAM')
        
        # self.cuisine.core.run('wget https://raw.github.com/ocaml/opam/master/shell/opam_installer.sh')
        self.cuisine.core.file_download('https://raw.github.com/ocaml/opam/master/shell/opam_installer.sh', to='$tmpDir/opam_installer.sh')
        self.cuisine.core.run('bash $tmpDir/opam_installer.sh $binDir %s' % self.ocaml_version, profile=True)
        
        cmd = 'opam init --root=%s --comp %s -a --dot-profile %s' % (self.opam_root, self.ocaml_version, self.cuisine.bash.profilePath)
        self.cuisine.core.run(cmd, profile=True)
        
        cmd = "opam config env --root=%s --dot-profile %s > $tmpDir/opam.env" % (self.opam_root, self.cuisine.bash.profilePath)
        self.cuisine.core.run(cmd, die=False, profile=True)
        
        opam_deps = """ocamlfind ssl.0.5.2 camlbz2 snappy sexplib bisect lwt.2.5.1 camltc \
        cstruct ctypes ctypes-foreign uuidm zarith mirage-no-xen.1 quickcheck.1.0.2 \
        cmdliner conf-libev depext kinetic-client tiny_json ppx_deriving.3.1 \
        ppx_deriving_yojson core.113.00.00 redis uri.1.9.1 result
        """
        
        self.cuisine.core.run_script('source $tmpDir/opam.env && opam update && opam install -y %s' % opam_deps, profile=True)

    def _install_deps_intel_storage(self):
        url = 'https://01.org/sites/default/files/downloads/intelr-storage-acceleration-library-open-source-version/isa-l-2.14.0.tar.gz'
        self.cuisine.core.file_download(url, to='$tmpDir/isa-l-2.14.0.tar.gz')

        self.cuisine.core.run('cd $tmpDir && tar xfzv isa-l-2.14.0.tar.gz')
        self.cuisine.core.run('cd $tmpDir/isa-l-2.14.0 && ./autogen.sh && ./configure')
        self.cuisine.core.run('cd $tmpDir/isa-l-2.14.0 && make && make install')
        
        """
        RUN wget https://01.org/sites/default/files/downloads/intelr-storage-acceleration-library-open-source-version/isa-l-2.14.0.tar.gz
        RUN tar xfzv isa-l-2.14.0.tar.gz
        RUN cd isa-l-2.14.0 && ./autogen.sh && ./configure
        RUN cd isa-l-2.14.0 && make
        RUN cd isa-l-2.14.0 && make install
        """
        return

    def _install_deps_cpp(self):
        self.cuisine.package.multiInstall("libgtest-dev cmake", allow_unauthenticated=True)
        self.cuisine.core.run('cd /usr/src/gtest && cmake . && make && mv libg* /usr/lib/')
        
        """
        RUN apt-get update && apt-get -y install libgtest-dev cmake
        RUN cd /usr/src/gtest \
            && cmake . \
            && make \
            && mv libg* /usr/lib/
        """

        return

    def _install_deps_arakoon(self):
        aradest = self.cuisine.git.pullRepo('https://github.com/openvstorage/arakoon.git', depth=None)
        pfx = 'cd %s && source $tmpDir/opam.env' % aradest
        
        self.cuisine.core.run('%s && git pull && git checkout tags/1.9.3' % pfx)
        self.cuisine.core.run('%s && make' % pfx)
        
        prefix = '%s/%s' % (self.opam_root, self.ocaml_version)
        libdir = 'ocamlfind printconf destdir'
        cmd = '%s && export PREFIX=%s && export OCAML_LIBDIR=`%s` && make install' % (pfx, prefix, libdir)
        
        self.cuisine.core.run_script(cmd, profile=True)
        
        """
        RUN git clone https://github.com/openvstorage/arakoon.git
        RUN cd arakoon && git pull && git checkout tags/1.9.3
        RUN cd arakoon && eval `${opam_env}` && make
        RUN cd arakoon && eval `${opam_env}` \
            && export PREFIX=${opam_root}/${ocaml_version} \
            && export OCAML_LIBDIR=`ocamlfind printconf destdir` \
            && make install
        """
        return

    def _install_deps_orocksdb(self):
        commit = '8bc61d8a451a2724399247abf76643aa7b2a07e9'
        orodest = self.cuisine.git.pullRepo('https://github.com/domsj/orocksdb.git', depth=None)
        pfx = 'cd %s && source $tmpDir/opam.env' % orodest

        self.cuisine.core.run('%s && git pull && git checkout %s' % (pfx, commit))
        self.cuisine.core.run('%s && ./install_rocksdb.sh && make build install' % pfx)
        
        """
        RUN git clone https://github.com/domsj/orocksdb.git \
            && eval `${opam_env}` \
            && cd orocksdb \
            && git checkout 8bc61d8a451a2724399247abf76643aa7b2a07e9 \
            && ./install_rocksdb.sh \
            && make build install
        """
        
        return

    def _install_deps_etcd(self):
        url = 'https://github.com/coreos/etcd/releases/download/v2.2.4/etcd-v2.2.4-linux-amd64.tar.gz'
        self.cuisine.core.file_download(url, to='$tmpDir/etcd-v2.2.4-linux-amd64.tar.gz')

        self.cuisine.core.run('cd $tmpDir && tar xfzv etcd-v2.2.4-linux-amd64.tar.gz')
        self.cuisine.core.run('cp $tmpDir/etcd-v2.2.4-linux-amd64/etcd /usr/bin')
        self.cuisine.core.run('cp $tmpDir/etcd-v2.2.4-linux-amd64/etcdctl /usr/bin')
        
        """
        RUN curl -L  https://github.com/coreos/etcd/releases/download/v2.2.4/etcd-v2.2.4-linux-amd64.tar.gz -o etcd-v2.2.4-linux-amd64.tar.gz
        RUN tar xzvf etcd-v2.2.4-linux-amd64.tar.gz
        RUN cp ./etcd-v2.2.4-linux-amd64/etcd /usr/bin \
            && cp ./etcd-v2.2.4-linux-amd64/etcdctl /usr/bin
        """
        
        return
        
    def _install_deps(self):
        self._install_deps_opam()
        self._install_deps_intel_storage()
        self._install_deps_cpp()
        self._install_deps_arakoon()
        self._install_deps_orocksdb()
        self._install_deps_etcd()

    def _build(self, version='6.0.0'):
        repo = self.cuisine.git.pullRepo('https://github.com/openvstorage/alba', depth=None)
        
        """
        str_repl = {
            'workspace': self.cuisine.core.dir_paths['tmpDir'],
            'version': version,
        }
        str_repl['volumedriver'] = self.cuisine.git.pullRepo('https://github.com/openvstorage/volumedriver', depth=None)
        str_repl['buildtools'] = self.cuisine.git.pullRepo('https://github.com/openvstorage/volumedriver-buildtools', depth=None)
        self.cuisine.core.run('cd %(volumedriver)s;git checkout tags/%(version)s' % str_repl)
        """

        build_script = """
        docker start build-ubuntu1604-alba
        ssh + cd alba/ && make
        
        ## docker run -i -t -e UID=${UID} -v ${PWD}:/home/jenkins/alba -w /home/jenkins/alba build-ubuntu1604-alba bash -l
        """
        
        print(build_script)
        
        # OUTPUT: ./ocaml/alba.native version
        
        # self.cuisine.core.run_script(build_script)
