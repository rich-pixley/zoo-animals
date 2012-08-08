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

# m h  dom mon dow   command
0 21 * * * za-post (/usr/bin/find /home/za-post -type d -mtime +3 -name oe-failure -print -exec rm -rf {} \; -prune 2>&1 ; echo done) | mail -s "post-commit checker `hostname` reap" zoo-animal-admin@mailman.palm.com
