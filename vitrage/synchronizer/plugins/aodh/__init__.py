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

OPTS = [
    cfg.StrOpt('transformer',
               default='vitrage.synchronizer.plugins.aodh.'
                       'transformer.AodhTransformer',
               help='Aodh plugin transformer class path',
               required=True),
    cfg.StrOpt('synchronizer',
               default='vitrage.synchronizer.plugins.aodh.synchronizer'
                       '.AodhSynchronizer',
               help='Aodh plugin synchronizer class path',
               required=True),
    cfg.IntOpt('changes_interval',
               default=30,
               min=30,
               help='interval between checking changes in aodh plugin',
               required=True),
    cfg.StrOpt('user', default='admin', help='Aodh user name'),
    cfg.StrOpt('password', default='password', help='Aodh user password'),
    cfg.StrOpt('url', default='http://localhost:5000/v2.0/',
               help='Aodh authentication url'),
    cfg.StrOpt('version', default='2', help='Aodh version'),
    cfg.StrOpt('project', default='admin', help='Aodh project'),
]
