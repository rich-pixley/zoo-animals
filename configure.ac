# Process this file with autoconf to produce a configure script.

# Time-stamp: <10-Jul-2012 11:25:54 PDT by rich.pixley@palm.com>

# Copyright (c) 2008 - 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

AC_INIT(zoo-animals, 0.0)
AC_PREREQ([2.61])
AC_COPYRIGHT([Copyright 2008 - 2012 Hewlett-Packard Development Company, L.P.])
AC_CONFIG_SRCDIR([za-conf/ZAconf-py.in])

AC_ARG_ENABLE([maintainer-mode], [AS_HELP_STRING([--enable-maintainer-mode],
				 does nothing; exists for compatibility)],
				 [], [])

AC_ARG_ENABLE([dependency-tracking], [AS_HELP_STRING([--enable-dependency-tracking],
				 does nothing; exists for compatibility)],
				 [], [])

AC_PROG_INSTALL
AC_PROG_MKDIR_P

AC_CONFIG_FILES([GNUmakefile:GNUmakefile.in])
AC_CONFIG_FILES([docs/Makefile:docs/Makefile.in])
AC_CONFIG_FILES([za-pre/tests/GNUmakefile:za-pre/tests/GNUmakefile.in])
AC_CONFIG_FILES([za-post/tests/GNUmakefile:za-post/tests/GNUmakefile.in])
AC_OUTPUT
