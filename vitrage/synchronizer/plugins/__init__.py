# Copyright 2016 - Nokia
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


# Register options for the service
OPTS = [
    cfg.StrOpt('static_plugins_dir',
               default='/etc/vitrage/static_plugins',
               help='A path for the static plugins for the synchronizer'
               ),
    cfg.StrOpt('nagios_user',
               help='Nagios user'
               ),
    cfg.StrOpt('nagios_password',
               help='Nagios password'
               ),
    cfg.StrOpt('nagios_url',
               help='Nagios url for querying the data. Example: '
               ' http://<ip>/monitoring/nagios/cgi-bin/status.cgi'
               ),
    cfg.StrOpt('nagios_config_file',
               default='/etc/vitrage/nagios_conf.yaml',
               help='Nagios configuration file'
               ),
]
