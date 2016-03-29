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

from vitrage.synchronizer.plugins.aodh import AODH_PLUGIN
from vitrage.synchronizer.plugins.cinder.volume import CINDER_VOLUME_PLUGIN
from vitrage.synchronizer.plugins.nagios import NAGIOS_PLUGIN
from vitrage.synchronizer.plugins.nova.host import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins.nova.instance import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins.nova.zone import NOVA_ZONE_PLUGIN
from vitrage.synchronizer.plugins.static_physical import STATIC_PHYSICAL_PLUGIN

OPENSTACK_NODE = 'openstack.node'

# Register options for the service
OPTS = [

    cfg.ListOpt('plugin_type',
                default=[NOVA_HOST_PLUGIN,
                         NOVA_INSTANCE_PLUGIN,
                         NOVA_ZONE_PLUGIN,
                         NAGIOS_PLUGIN,
                         STATIC_PHYSICAL_PLUGIN,
                         AODH_PLUGIN,
                         CINDER_VOLUME_PLUGIN],
                help='Names of supported plugins'),
    cfg.ListOpt('plugin_path',
                default=['vitrage.synchronizer.plugins'],
                help='base path for plugins')
]
