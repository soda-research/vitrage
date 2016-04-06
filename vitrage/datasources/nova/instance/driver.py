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
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources.nova.nova_driver_base import NovaDriverBase

LOG = logging.getLogger(__name__)


class InstanceDriver(NovaDriverBase):

    @staticmethod
    def extract_events(instances):
        return [instance.__dict__ for instance in instances]

    def get_all(self, sync_mode):
        return self.make_pickleable(
            self.extract_events(self.client.servers.list()),
            NOVA_INSTANCE_DATASOURCE,
            sync_mode,
            'manager')

    @staticmethod
    def enrich_event(event, event_type):
        event[SyncProps.EVENT_TYPE] = event_type

        return InstanceDriver.make_pickleable([event],
                                              NOVA_INSTANCE_DATASOURCE,
                                              SyncMode.UPDATE)[0]

    @staticmethod
    def get_event_types(conf):
        return ['compute.instance']

    @staticmethod
    def get_skipped_event_types():
        return ['compute.instance.exists', 'compute.instance.update']

    @staticmethod
    def get_topic(conf):
        return conf[NOVA_INSTANCE_DATASOURCE].notification_topic
