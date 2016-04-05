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
from vitrage.common.constants import VertexProperties as VProps
from vitrage.synchronizer.plugins import NAGIOS_PLUGIN
from vitrage.synchronizer.plugins import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins import NOVA_ZONE_PLUGIN
from vitrage.tests.functional.data_sources.base import \
    TestDataSourcesBase
from vitrage.tests.mocks import mock_syncronizer as mock_sync


class TestNagios(TestDataSourcesBase):

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=[NAGIOS_PLUGIN,
                             NOVA_HOST_PLUGIN,
                             NOVA_INSTANCE_PLUGIN,
                             NOVA_ZONE_PLUGIN,
                             NAGIOS_PLUGIN],
                    help='Names of supported driver data sources'),

        cfg.ListOpt('plugin_path',
                    default=['vitrage.synchronizer.plugins'],
                    help='base path for data sources')
    ]

    @classmethod
    def setUpClass(cls):
        super(TestNagios, cls).setUpClass()
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.PLUGINS_OPTS, group='plugins')
        cls.load_plugins(cls.conf)

    def test_nagios_validity(self):
        # Setup
        processor = self._create_processor_with_graph(self.conf)
        self.assertEqual(self._num_total_expected_vertices(),
                         len(processor.entity_graph))

        spec_list = mock_sync.simple_nagios_alarm_generators(
            host_num=1,
            events_num=1)
        static_events = mock_sync.generate_random_events_list(spec_list)
        nagios_event = static_events[0]
        nagios_event['resource_name'] = \
            self._find_entity_id_by_type(processor.entity_graph,
                                         NOVA_HOST_PLUGIN)
        nagios_event['status'] = 'critical'

        # Action
        processor.process_event(nagios_event)

        # Test assertions
        self.assertEqual(self._num_total_expected_vertices() + 1,
                         len(processor.entity_graph))

        nagios_vertices = processor.entity_graph.get_vertices(
            vertex_attr_filter={
                VProps.CATEGORY: EntityCategory.ALARM,
                VProps.TYPE: NAGIOS_PLUGIN
            })
        self.assertEqual(1, len(nagios_vertices))

        nagios_neighbors = processor.entity_graph.neighbors(
            nagios_vertices[0].vertex_id)
        self.assertEqual(1, len(nagios_neighbors))

        self.assertEqual(NOVA_HOST_PLUGIN,
                         nagios_neighbors[0][VProps.TYPE])
