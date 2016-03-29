# Copyright 2016 - Alcatel-Lucent
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.synchronizer.plugins.nova.base import NovaBase
from vitrage.synchronizer.plugins.nova.instance import NOVA_INSTANCE_PLUGIN

LOG = logging.getLogger(__name__)


class InstanceSynchronizer(NovaBase):

    @staticmethod
    def extract_events(instances):
        return [instance.__dict__ for instance in instances]

    def get_all(self, sync_mode):
        return self.make_pickleable(
            self.extract_events(self.client.servers.list()),
            NOVA_INSTANCE_PLUGIN,
            sync_mode,
            'manager')

    @staticmethod
    def enrich_event(event, event_type):
        event[SyncProps.EVENT_TYPE] = event_type

        return InstanceSynchronizer.make_pickleable([event],
                                                    NOVA_INSTANCE_PLUGIN,
                                                    SyncMode.UPDATE)[0]

    @staticmethod
    def get_event_types(conf):
        return ['compute.instance']

    @staticmethod
    def get_topic(conf):
        return conf[NOVA_INSTANCE_PLUGIN].notification_topic
