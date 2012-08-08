# ad hoc place to keep notes about build specific stuff

set -e

case "$1" in
    name)
    	# return the name of this build
    	echo "Null Build"
	;;

    location)
    	# return the location of the source for this build
	echo Nowhere.
	;;

    topoftree)
    	echo Top
	;;

    co) # check out source code.  args: revision
    	set -x
	[ -d Build ] || mkdir Build
	: $0 co $2
	;;

    builddirname) echo Build ;;

    build)
    	# actually configure and do the build, presumably
    	# incrementally, presumably idempotently. Output goes to log.
    	set -x
	: $0 build
    	;;

    notify) # args are closures (not yet used)
    	set -x
	: $0 notify
    	;;

    *)
    	echo Unrecognized arguments: $*
	exit 1
	;;
esac
