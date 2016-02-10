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

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.entity_graph.processor import processor as proc

from vitrage.tests import base

from vitrage.tests.mocks import mock_syncronizer as mock_sync


class TestEntityGraph(base.BaseTest):

    NUM_NODES = 1
    NUM_ZONES = 2
    NUM_HOSTS = 4
    NUM_INSTANCES = 15

    def _create_processor_with_graph(self, processor=None):
        events = self._create_mock_events()

        if not processor:
            processor = proc.Processor()

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

    def _num_total_expected_vertices(self):
        return self.NUM_NODES + self.NUM_ZONES + self.NUM_HOSTS + \
            self.NUM_INSTANCES
