# Copyright 2016 - Alcatel-Lucent
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


import vitrage.common.constants as cons
from vitrage.entity_graph.transformer import base as tbase
from vitrage.entity_graph.transformer.base import TransformerBase
from vitrage.entity_graph.transformer import nova_transformers
from vitrage.entity_graph.transformer.nova_transformers import ZoneTransformer
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)


class NovaZoneTransformerTest(base.BaseTest):

    def test_create_placeholder_vertex(self):

        LOG.debug('Zone transformer test: create placeholder vertex')

        zone_name = 'zone123'
        timestamp = datetime.datetime.utcnow()

        zt = nova_transformers.ZoneTransformer()
        placeholder = zt.create_placeholder_vertex(
            zone_name,
            timestamp
        )

        observed_id_values = placeholder.vertex_id.split(
            TransformerBase.KEY_SEPARATOR)
        expected_id_values = zt.key_values([zone_name])
        self.assertEqual(observed_id_values, expected_id_values)

        observed_time = placeholder.get(
            cons.VertexProperties.UPDATE_TIMESTAMP
        )
        self.assertEqual(observed_time, timestamp)

        observed_subtype = placeholder.get(
            cons.VertexProperties.SUBTYPE
        )
        self.assertEqual(observed_subtype, nova_transformers.ZONE_SUBTYPE)

        observed_entity_id = placeholder.get(
            cons.VertexProperties.ID
        )
        self.assertEqual(observed_entity_id, zone_name)

        observed_type = placeholder.get(
            cons.VertexProperties.TYPE
        )
        self.assertEqual(observed_type, cons.EntityTypes.RESOURCE)

        is_placeholder = placeholder.get(
            cons.VertexProperties.IS_PLACEHOLDER
        )
        self.assertEqual(is_placeholder, True)

    def test_key_values(self):

        LOG.debug('Zone transformer test: get key values')

        zone_name = 'zone123'
        observed_key_fields = nova_transformers.ZoneTransformer().key_values(
            [zone_name]
        )

        self.assertEqual(cons.EntityTypes.RESOURCE, observed_key_fields[0])
        self.assertEqual(
            nova_transformers.ZONE_SUBTYPE,
            observed_key_fields[1]
        )
        self.assertEqual(zone_name, observed_key_fields[2])

    def test_extract_key(self):
        pass

    def test_snapshot_transform(self):

        LOG.debug('Nova zone transformer test: transform entity event')

        spec_list = mock_sync.simple_zone_generators(
            zone_num=2,
            host_num=3,
            snapshot_events=5
        )
        zone_events = mock_sync.generate_random_events_list(spec_list)

        for event in zone_events:
            wrapper = nova_transformers.ZoneTransformer().transform(event)
            vertex = wrapper.vertex
            self._validate_vertex_props(vertex, event)

            neighbors = wrapper.neighbors
            self._validate_neighbors(neighbors, vertex.vertex_id, event)

    def _validate_neighbors(self, neighbors, zone_vertex_id, event):

        node_neighbors_counter = 0

        for neighbor in neighbors:
            vertex_subtype = neighbor.vertex.get(cons.VertexProperties.SUBTYPE)

            if tbase.NODE_SUBTYPE == vertex_subtype:
                node_neighbors_counter += 1
                self._validate_node_neighbor(neighbor, zone_vertex_id)
            else:
                hosts = tbase.extract_field_value(event, ('hosts',))
                self._validate_host_neighbor(neighbor,
                                             zone_vertex_id,
                                             hosts,
                                             event['sync_mode'])

        self.assertEqual(1,
                         node_neighbors_counter,
                         'Zone can belongs to only one Node')

    def _validate_host_neighbor(self,
                                host_neighbor,
                                zone_vertex_id,
                                hosts,
                                sync_mode):

        host_vertex = host_neighbor.vertex
        host_vertex_id = host_vertex.get(cons.VertexProperties.ID)

        host_dic = hosts[host_vertex_id]
        self.assertIsNotNone(hosts[host_vertex_id])

        host_available = tbase.extract_field_value(
            host_dic,
            nova_transformers.ZoneTransformer.HOST_AVAILABLE[sync_mode]
        )
        host_active = tbase.extract_field_value(
            host_dic,
            nova_transformers.ZoneTransformer.HOST_ACTIVE[sync_mode]
        )
        expected_host_state = host_available and host_active
        self.assertEqual(
            expected_host_state,
            host_vertex.get(cons.VertexProperties.STATE)
        )

        is_placeholder = host_vertex[cons.VertexProperties.IS_PLACEHOLDER]
        self.assertFalse(is_placeholder)

        is_deleted = host_vertex[cons.VertexProperties.IS_DELETED]
        self.assertFalse(is_deleted)

        # Validate neighbor edge
        edge = host_neighbor.edge
        self.assertEqual(edge.target_id, host_neighbor.vertex.vertex_id)
        self.assertEqual(edge.source_id, zone_vertex_id)
        self.assertEqual(edge.label, cons.EdgeLabels.CONTAINS)

    def _validate_node_neighbor(self, node_neighbor, zone_vertex_id):

        expected_node_neighbor = tbase.create_node_placeholder_vertex()
        self.assertEqual(expected_node_neighbor, node_neighbor.vertex)

        # Validate neighbor edge
        edge = node_neighbor.edge
        self.assertEqual(edge.source_id, node_neighbor.vertex.vertex_id)
        self.assertEqual(edge.target_id, zone_vertex_id)
        self.assertEqual(edge.label, cons.EdgeLabels.CONTAINS)

    def _validate_vertex_props(self, vertex, event):

        # zt = nova_transformers.ZoneTransformer

        sync_mode = event['sync_mode']
        extract_value = tbase.extract_field_value

        expected_id = extract_value(
            event,
            ZoneTransformer().ZONE_NAME[sync_mode]
        )
        observed_id = vertex[cons.VertexProperties.ID]
        self.assertEqual(expected_id, observed_id)

        self.assertEqual(
            cons.EntityTypes.RESOURCE,
            vertex[cons.VertexProperties.TYPE]
        )

        self.assertEqual(
            nova_transformers.ZONE_SUBTYPE,
            vertex[cons.VertexProperties.SUBTYPE]
        )

        expected_timestamp = extract_value(
            event,
            ZoneTransformer().TIMESTAMP[sync_mode]
        )
        observed_timestamp = vertex[cons.VertexProperties.UPDATE_TIMESTAMP]
        self.assertEqual(expected_timestamp, observed_timestamp)

        expected_name = extract_value(
            event,
            ZoneTransformer().ZONE_NAME[sync_mode]
        )
        observed_name = vertex[cons.VertexProperties.NAME]
        self.assertEqual(expected_name, observed_name)

        is_zone_available = extract_value(
            event,
            ZoneTransformer().ZONE_STATE[sync_mode]
        )

        if is_zone_available:
            expected_state = ZoneTransformer.STATE_AVAILABLE
        else:
            expected_state = ZoneTransformer.STATE_UNAVAILABLE

        observed_state = vertex[cons.VertexProperties.STATE]
        self.assertEqual(expected_state, observed_state)

        is_placeholder = vertex[cons.VertexProperties.IS_PLACEHOLDER]
        self.assertFalse(is_placeholder)

        is_deleted = vertex[cons.VertexProperties.IS_DELETED]
        self.assertFalse(is_deleted)
