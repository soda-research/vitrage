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
from vitrage.synchronizer.plugins import CINDER_VOLUME_PLUGIN
from vitrage.synchronizer.plugins import NAGIOS_PLUGIN
from vitrage.synchronizer.plugins import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins import NOVA_ZONE_PLUGIN
from vitrage.tests.functional.data_sources.base import \
    TestDataSourcesBase
from vitrage.tests.mocks import mock_syncronizer as mock_sync


class TestCinderVolume(TestDataSourcesBase):

    PLUGINS_OPTS = [
        cfg.ListOpt('plugin_type',
                    default=[NAGIOS_PLUGIN,
                             NOVA_HOST_PLUGIN,
                             NOVA_INSTANCE_PLUGIN,
                             NOVA_ZONE_PLUGIN,
                             CINDER_VOLUME_PLUGIN],
                    help='Names of supported driver data sources'),

        cfg.ListOpt('plugin_path',
                    default=['vitrage.synchronizer.plugins'],
                    help='base path for data sources')
    ]

    @classmethod
    def setUpClass(cls):
        super(TestCinderVolume, cls).setUpClass()
        cls.conf = cfg.ConfigOpts()
        cls.conf.register_opts(cls.PROCESSOR_OPTS, group='entity_graph')
        cls.conf.register_opts(cls.PLUGINS_OPTS, group='plugins')
        cls.load_plugins(cls.conf)

    def test_cinder_volume_validity(self):
        # Setup
        processor = self._create_processor_with_graph(self.conf)
        self.assertEqual(self._num_total_expected_vertices(),
                         len(processor.entity_graph))

        spec_list = mock_sync.simple_volume_generators(
            volume_num=1,
            instance_num=1,
            snapshot_events=1)
        static_events = mock_sync.generate_random_events_list(spec_list)
        cinder_volume_event = static_events[0]
        cinder_volume_event['attachments'][0]['server_id'] = \
            self._find_entity_id_by_type(processor.entity_graph,
                                         NOVA_INSTANCE_PLUGIN)

        # Action
        processor.process_event(cinder_volume_event)

        # Test assertions
        self.assertEqual(self._num_total_expected_vertices() + 1,
                         len(processor.entity_graph))

        cinder_vertices = processor.entity_graph.get_vertices(
            vertex_attr_filter={
                VProps.CATEGORY: EntityCategory.RESOURCE,
                VProps.TYPE: CINDER_VOLUME_PLUGIN
            })
        self.assertEqual(1, len(cinder_vertices))

        cinder_neighbors = processor.entity_graph.neighbors(
            cinder_vertices[0].vertex_id)
        self.assertEqual(1, len(cinder_neighbors))

        self.assertEqual(NOVA_INSTANCE_PLUGIN,
                         cinder_neighbors[0][VProps.TYPE])
