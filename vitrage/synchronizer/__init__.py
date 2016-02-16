# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

OPTS = [
    cfg.IntOpt('snapshots_interval',
               default=600,
               min=10,
               help='interval between full snapshots'),
    cfg.IntOpt('nagios_changes_interval',
               default=30,
               min=30,
               help='interval between checking changes in nagios plugin'),
    cfg.IntOpt('static_physical_changes_interval',
               default=30,
               min=30,
               help='interval between checking changes in the configuration '
                    'files of the physical topology plugin'),
]
