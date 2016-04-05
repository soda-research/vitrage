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
from vitrage.common.constants import VertexProperties as VProps
from vitrage.synchronizer.plugins import NAGIOS_PLUGIN
from vitrage.synchronizer.plugins import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins import NOVA_ZONE_PLUGIN
from vitrage.synchronizer.plugins.static_physical import STATIC_PHYSICAL_PLUGIN
from vitrage.synchronizer.plugins.static_physical import SWITCH
from vitrage.tests.functional.data_sources.base import \
    TestDataSourcesBase
from vitrage.tests.mocks import mock_syncronizer as mock_sync


class TestStaticPhysical(TestDataSourcesBase):

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=[NAGIOS_PLUGIN,
                             NOVA_HOST_PLUGIN,
                             NOVA_INSTANCE_PLUGIN,
                             NOVA_ZONE_PLUGIN,
                             STATIC_PHYSICAL_PLUGIN],
                    help='Names of supported driver data sources'),

        cfg.ListOpt('plugin_path',
                    default=['vitrage.synchronizer.plugins'],
                    help='base path for data sources')
    ]

    @classmethod
    def setUpClass(cls):
        super(TestStaticPhysical, cls).setUpClass()
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.PLUGINS_OPTS, group='plugins')
        cls.load_plugins(cls.conf)

    def test_static_physical_validity(self):
        # Setup
        processor = self._create_processor_with_graph(self.conf)
        processor.transformer_manager.transformers[SWITCH] = \
            processor.transformer_manager.transformers[STATIC_PHYSICAL_PLUGIN]
        self.assertEqual(self._num_total_expected_vertices(),
                         len(processor.entity_graph))

        spec_list = mock_sync.simple_switch_generators(
            switch_num=1,
            host_num=1,
            snapshot_events=1)
        static_events = mock_sync.generate_random_events_list(spec_list)
        static_physical_event = static_events[0]
        static_physical_event[SyncProps.SYNC_TYPE] = SWITCH
        static_physical_event['relationships'][0]['name'] = \
            self._find_entity_id_by_type(processor.entity_graph,
                                         NOVA_HOST_PLUGIN)

        # Action
        processor.process_event(static_physical_event)

        # Test assertions
        self.assertEqual(self._num_total_expected_vertices() + 1,
                         len(processor.entity_graph))

        static_physical_vertices = processor.entity_graph.get_vertices(
            vertex_attr_filter={
                VProps.CATEGORY: EntityCategory.RESOURCE,
                VProps.TYPE: SWITCH
            })
        self.assertEqual(1, len(static_physical_vertices))

        static_physical_neighbors = processor.entity_graph.neighbors(
            static_physical_vertices[0].vertex_id)
        self.assertEqual(1, len(static_physical_neighbors))

        self.assertEqual(NOVA_HOST_PLUGIN,
                         static_physical_neighbors[0][VProps.TYPE])
