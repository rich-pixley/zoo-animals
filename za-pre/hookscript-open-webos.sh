# ad hoc place to keep notes about build specific stuff
# Time-stamp: <21-Jun-2012 15:06:39 PDT by rich.pixley@palm.com>

set -e

gitloc=git@github.com:openwebos/webos.git
builddirname=webos

case "$1" in
    name)
    	# return the name of this build
    	echo "Open Webos"
	;;

    location)
    	# return the location of the source for this build
	echo "${gitloc}"
	;;

    topoftree)
    	# Hm.  Git can't tell top of tree remotely... I don't think...
    	# no mind... force a tree out, then use it to tell top of remote.
    	$0 co > /dev/null 2>&1
	cd ${builddirname}
	git log -1 remotes/origin/HEAD --format=format:%h%n
	;;

    co)
    	# check out source code, produce a working directory.
    	[ -d ${builddirname}/.git ] || git clone ${gitloc}
	cd ${builddirname}
	git fetch origin
	;;

    builddirname) echo ${builddirname} ;;

    build)
    	# actually configure and do the build, presumably
    	# incrementally, presumably idempotently. Output goes to log.
    	set -x
	./mcf --enable-parallel-make=8 --enable-bb-number-threads=8 qemuarm qemumips qemuppc #qemux86 qemux86_64
	make
    	;;

    *)
    	echo Unrecognized arguments: $*
	exit 1
	;;
esac
