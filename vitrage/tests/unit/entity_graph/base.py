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

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.datetime_utils import utcnow
from vitrage.entity_graph.initialization_status import InitializationStatus
from vitrage.entity_graph.processor import processor as proc
import vitrage.graph.utils as graph_utils
from vitrage.service import load_plugin
from vitrage.tests import base
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.mocks import utils


class TestEntityGraphUnitBase(base.BaseTest):

    PROCESSOR_OPTS = [
        cfg.StrOpt('states_plugins_dir',
                   default=utils.get_resources_dir() + '/states_plugins'),
    ]

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=['nagios',
                             'nova.host',
                             'nova.instance',
                             'nova.zone'],
                    help='Names of supported synchronizer plugins'),
    ]

    NOVA_INSTANCE = 'nova.instance'
    NOVA_HOST = 'nova.host'
    NOVA_ZONE = 'nova.zone'
    NAGIOS = 'nagios'

    NUM_NODES = 1
    NUM_ZONES = 2
    NUM_HOSTS = 4
    NUM_INSTANCES = 16

    @staticmethod
    def load_plugins(conf):
        for plugin_name in conf.synchronizer_plugins.plugin_type:
            load_plugin(conf, plugin_name)

    def _create_processor_with_graph(self, conf, processor=None):
        events = self._create_mock_events()

        if not processor:
            processor = proc.Processor(conf, InitializationStatus())

        for event in events:
            processor.process_event(event)

        return processor

    def _create_mock_events(self):
        gen_list = mock_sync.simple_zone_generators(
            self.NUM_ZONES,
            self.NUM_HOSTS,
            snapshot_events=self.NUM_ZONES,
            snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        gen_list += mock_sync.simple_host_generators(
            self.NUM_ZONES,
            self.NUM_HOSTS,
            self.NUM_HOSTS,
            snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        gen_list += mock_sync.simple_instance_generators(
            self.NUM_HOSTS,
            self.NUM_INSTANCES,
            self.NUM_INSTANCES,
            snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        return mock_sync.generate_sequential_events_list(gen_list)

    def _create_entity(self, processor=None, spec_type=None, sync_mode=None,
                       event_type=None, properties=None):
        # create instance event with host neighbor
        event = self._create_event(spec_type=spec_type,
                                   sync_mode=sync_mode,
                                   event_type=event_type,
                                   properties=properties)

        # add instance entity with host
        if processor is None:
            processor = proc.Processor(self.conf, InitializationStatus())

        vertex, neighbors, event_type = processor.transform_entity(event)
        processor.create_entity(vertex, neighbors)

        return vertex, neighbors, processor

    @staticmethod
    def _create_event(spec_type=None, sync_mode=None,
                      event_type=None, properties=None):
        # generate event
        spec_list = mock_sync.simple_instance_generators(1, 1, 1)
        events_list = mock_sync.generate_random_events_list(
            spec_list)

        # update properties
        if sync_mode is not None:
            events_list[0][SyncProps.SYNC_MODE] = sync_mode

        if event_type is not None:
            events_list[0][SyncProps.EVENT_TYPE] = event_type

        if properties is not None:
            for key, value in properties.iteritems():
                events_list[0][key] = value

        return events_list[0]

    @staticmethod
    def _create_alarm(vitrage_id, alarm_type):
        return graph_utils.create_vertex(
            vitrage_id,
            entity_id=vitrage_id,
            entity_category=EntityCategory.ALARM,
            entity_type=alarm_type,
            entity_state='active',
            is_deleted=False,
            sample_timestamp=utcnow(),
            is_placeholder=False,
        )

    def _num_total_expected_vertices(self):
        return self.NUM_NODES + self.NUM_ZONES + self.NUM_HOSTS + \
            self.NUM_INSTANCES
