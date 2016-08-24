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

from oslo_log import log as logging

from vitrage import clients
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import SyncMode
from vitrage.datasources.cinder.volume import CINDER_VOLUME_DATASOURCE
from vitrage.datasources.driver_base import DriverBase
from vitrage.datasources.heat.stack import HEAT_STACK_DATASOURCE
from vitrage.datasources.neutron.network import NEUTRON_NETWORK_DATASOURCE
from vitrage.datasources.neutron.port import NEUTRON_PORT_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE

LOG = logging.getLogger(__name__)


class HeatStackDriver(DriverBase):

    FAILED = 'FAILED'

    RESOURCE_TYPE_CONVERSION = {
        'OS::Nova::Server': NOVA_INSTANCE_DATASOURCE,
        'OS::Cinder::Volume': CINDER_VOLUME_DATASOURCE,
        'OS::Neutron::Net': NEUTRON_NETWORK_DATASOURCE,
        'OS::Neutron::Port': NEUTRON_PORT_DATASOURCE
    }

    def __init__(self, conf):
        super(HeatStackDriver, self).__init__()
        self._client = None
        self.conf = conf
        self._filter_resource_types()

    @property
    def client(self):
        if not self._client:
            self._client = clients.heat_client(self.conf)
        return self._client

    @staticmethod
    def get_topic(conf):
        return conf[HEAT_STACK_DATASOURCE].notification_topic

    @staticmethod
    def get_event_types(conf):
        return ['orchestration.stack.create.end',
                'orchestration.stack.delete.end',
                'orchestration.stack.update.error',
                'orchestration.stack.update.end',
                'orchestration.stack.suspend.error',
                'orchestration.stack.suspend.end',
                'orchestration.stack.resume.error',
                'orchestration.stack.resume.end']

    @staticmethod
    def enrich_event(event, event_type):
        # TODO(Nofar): add call to get resources of the stack if not deleted
        # change transformer that if delete we remove the stack from the graph
        # and hence all the edges to it

        event[DSProps.EVENT_TYPE] = event_type

        return HeatStackDriver.make_pickleable([event],
                                               HEAT_STACK_DATASOURCE,
                                               SyncMode.UPDATE)[0]

    def _filter_resource_types(self):
        types = self.conf.datasources.types
        tmp_dict = {}

        for key, value in self.RESOURCE_TYPE_CONVERSION.items():
            if value in types:
                tmp_dict[key] = value

        self.RESOURCE_TYPE_CONVERSION = tmp_dict

    def _make_stacks_list(self, stacks):
        stacks_list = []
        for stack in stacks:
            stack_dict = stack.__dict__
            if self.FAILED not in stack_dict['stack_status']:
                stacks_list.append(stack_dict)
        return stacks_list

    def _append_stacks_resources(self, stacks):
        updated_stacks = []
        for stack in stacks:
            resources = self. client.resources.list(stack['id'])
            new_stack = stack
            new_stack['resources'] = []
            for resource in resources:
                resource_dict = resource.__dict__
                if resource_dict['resource_type'] in \
                        self.RESOURCE_TYPE_CONVERSION.keys():
                    new_stack['resources'].append(resource_dict)
            # LOG.error("Resources were attached to stack: %s", new_stack)
            updated_stacks.append(new_stack)
        return updated_stacks

    def get_all(self, sync_mode):
        stacks = self.client.stacks.list(global_tenant=True)
        stacks_list = self._make_stacks_list(stacks)
        stacks_with_resources = self._append_stacks_resources(stacks_list)
        return self.make_pickleable(stacks_with_resources,
                                    HEAT_STACK_DATASOURCE,
                                    sync_mode,
                                    'manager')
