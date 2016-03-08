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
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_config import cfg

OPTS = [
    cfg.StrOpt('transformer',
               default='vitrage.synchronizer.plugins.static_physical.'
                       'transformer.StaticPhysicalTransformer',
               help='Static physical transformer class path',
               required=True),
    cfg.StrOpt('synchronizer',
               default='vitrage.synchronizer.plugins.static_physical'
                       '.synchronizer.StaticPhysicalSynchronizer',
               help='Static physical synchronizer class path',
               required=True),
    cfg.IntOpt('changes_interval',
               default=30,
               min=30,
               help='interval between checking changes in the configuration'
                    'files of the physical topology plugin',
               required=True),
    cfg.StrOpt('directory', default='/etc/vitrage/static_plugins',
               help='Static physical plugins directory'),
    cfg.ListOpt('entities',
                default=['switch'],
                help='Static physical entity types list')
]
