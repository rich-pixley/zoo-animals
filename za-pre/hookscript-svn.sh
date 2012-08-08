# ad hoc place to keep notes about build specific stuff

set -e

svnloc=http://subversion.palm.com/main/nova/oe/trunk

case "$1" in
    name)
    	# return the name of this build
    	echo "Classic Nova"
	;;

    location)
    	# return the location of the source for this build
	echo "${svnloc}"
	;;

    topoftree)
    	# returns revision of latest changeset
	if [ -e ${topoftreefile} ] ; then
	    [ ${topoftreefile} -nt ${svnlocfile} ] || echo ${svnlocfile} changed > ${priorityfullfile}
	fi

	svn log --limit 1 ${svnloc} > ${topoftreefile}

	sed -n -e '2s/^r\([0-9]*\).*$/\1/p' < ${topoftreefile}
	;;

    co)
    	# check out source code
    	:
	;;

    build)
    	# actually configure and do the build, presumably
    	# incrementally, presumably idempotently. Output goes to log.
    	set -x
    	./mcf --primary
	make ${makeargs}
	    && ./mcf 
	    && time make

    	;;

    notify) # args are closures
    	;;

    *)
    	echo Unrecognized arguments: $*
	exit 1
	;;
esac
