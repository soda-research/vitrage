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

import datetime

from oslo_log import log as logging

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.synchronizer.plugins.nova.host.transformer import HostTransformer
from vitrage.synchronizer.plugins.static_physical.transformer \
    import StaticPhysical
from vitrage.synchronizer.plugins.transformer_base import TransformerBase
from vitrage.tests import base
from vitrage.tests.mocks import mock_syncronizer as mock_sync

LOG = logging.getLogger(__name__)


class TestStaticPhysicalTransformer(base.BaseTest):

    def setUp(self):
        super(TestStaticPhysicalTransformer, self).setUp()

        self.transformers = {}
        host_transformer = HostTransformer(self.transformers)
        static_transformer = StaticPhysical(self.transformers)
        self.transformers[EntityType.NOVA_HOST] = host_transformer
        self.transformers[EntityType.SWITCH] = static_transformer

    def test_create_placeholder_vertex(self):

        LOG.debug('Static Physical transformer test: Create placeholder '
                  'vertex')

        # Test setup
        switch_type = EntityType.SWITCH
        switch_name = 'switch-1'
        timestamp = datetime.datetime.utcnow()
        static_transformer = StaticPhysical(self.transformers)

        # Test action
        properties = {
            VProps.TYPE: switch_type,
            VProps.ID: switch_name,
            VProps.UPDATE_TIMESTAMP: timestamp
        }
        placeholder = static_transformer.create_placeholder_vertex(properties)

        # Test assertions
        observed_id_values = placeholder.vertex_id.split(
            TransformerBase.KEY_SEPARATOR)
        expected_id_values = \
            StaticPhysical(self.transformers).key_values(
                [switch_type, switch_name])
        self.assertEqual(observed_id_values, expected_id_values)

        observed_time = placeholder.get(VProps.UPDATE_TIMESTAMP)
        self.assertEqual(observed_time, timestamp)

        observed_subtype = placeholder.get(VProps.TYPE)
        self.assertEqual(observed_subtype, switch_type)

        observed_entity_id = placeholder.get(VProps.ID)
        self.assertEqual(observed_entity_id, switch_name)

        observed_category = placeholder.get(VProps.CATEGORY)
        self.assertEqual(observed_category, EntityCategory.RESOURCE)

        is_placeholder = placeholder.get(VProps.IS_PLACEHOLDER)
        self.assertEqual(is_placeholder, True)

    def test_key_values(self):
        LOG.debug('Static Physical transformer test: get key values')

        # Test setup
        switch_type = EntityType.SWITCH
        switch_name = 'switch-1'
        static_transformer = StaticPhysical(self.transformers)

        # Test action
        observed_key_fields = static_transformer.key_values(
            [switch_type,
             switch_name])

        # Test assertions
        self.assertEqual(EntityCategory.RESOURCE, observed_key_fields[0])
        self.assertEqual(EntityType.SWITCH, observed_key_fields[1])
        self.assertEqual(switch_name, observed_key_fields[2])

    def test_snapshot_transform(self):
        LOG.debug('Static Physical transformer test: transform entity event '
                  'snapshot')

        # Test setup
        spec_list = mock_sync.simple_switch_generators(2, 10, 10)
        static_events = mock_sync.generate_random_events_list(spec_list)

        for event in static_events:
            # Test action
            wrapper = StaticPhysical(self.transformers).transform(event)

            # Test assertions
            vertex = wrapper.vertex
            self._validate_switch_vertex_props(vertex, event)

            neighbors = wrapper.neighbors
            self._validate_neighbors(neighbors, vertex.vertex_id, event)

    def _validate_neighbors(self, neighbors, switch_vertex_id, event):
        host_counter = 0

        for neighbor in neighbors:
            self._validate_host_neighbor(neighbor,
                                         event['relationships'][host_counter],
                                         switch_vertex_id)
            host_counter += 1

        self.assertEqual(5,
                         host_counter,
                         'Zone can belongs to only one Node')

    def _validate_host_neighbor(self,
                                host_neighbor,
                                host_event,
                                switch_vertex_id):
        # validate neighbor vertex
        self._validate_host_vertex_props(host_neighbor.vertex, host_event)

        # Validate neighbor edge
        edge = host_neighbor.edge
        self.assertEqual(edge.target_id, switch_vertex_id)
        self.assertEqual(edge.source_id, host_neighbor.vertex.vertex_id)
        self.assertEqual(edge.label, EdgeLabels.CONTAINS)

    def _validate_common_vertex_props(self, vertex, event):
        self.assertEqual(EntityCategory.RESOURCE, vertex[VProps.CATEGORY])
        self.assertEqual(event[SyncProps.SYNC_TYPE], vertex[VProps.TYPE])
        self.assertEqual(event[VProps.ID], vertex[VProps.ID])

    def _validate_switch_vertex_props(self, vertex, event):
        self._validate_common_vertex_props(vertex, event)
        self.assertEqual(event[SyncProps.SAMPLE_DATE],
                         vertex[VProps.UPDATE_TIMESTAMP])
        self.assertEqual(event[VProps.NAME], vertex[VProps.NAME])
        self.assertEqual(event[VProps.STATE], vertex[VProps.STATE])
        self.assertFalse(vertex[VProps.IS_PLACEHOLDER])
        self.assertFalse(vertex[VProps.IS_DELETED])

    def _validate_host_vertex_props(self, vertex, event):
        self._validate_common_vertex_props(vertex, event)
        self.assertTrue(vertex[VProps.IS_PLACEHOLDER])
        self.assertFalse(vertex[VProps.IS_DELETED])
