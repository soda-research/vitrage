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

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityTypes
from vitrage.common.constants import EventAction
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.transformer import base as tbase
from vitrage.entity_graph.transformer.base import TransformerBase
from vitrage.entity_graph.transformer import nova_transformers
from vitrage.entity_graph.transformer.nova_transformers import HostTransformer
from vitrage.tests.mocks import mock_syncronizer as mock_sync
from vitrage.tests.unit import base


LOG = logging.getLogger(__name__)


class NovaHostTransformerTest(base.BaseTest):

    def test_create_placeholder_vertex(self):
        LOG.debug('Nova host transformer test: Test create placeholder vertex')

        # Test setup
        host_name = 'host123'
        timestamp = datetime.datetime.utcnow()

        # Test action
        placeholder = HostTransformer().create_placeholder_vertex(
            host_name,
            timestamp
        )

        # Test assertions
        observed_id_values = placeholder.vertex_id.split(
            TransformerBase.KEY_SEPARATOR)
        expected_id_values = HostTransformer()._key_values([host_name])
        self.assertEqual(observed_id_values, expected_id_values)

        observed_time = placeholder.get(VertexProperties.UPDATE_TIMESTAMP)
        self.assertEqual(observed_time, timestamp)

        observed_subtype = placeholder.get(VertexProperties.TYPE)
        self.assertEqual(observed_subtype, nova_transformers.HOST_TYPE)

        observed_entity_id = placeholder.get(VertexProperties.ID)
        self.assertEqual(observed_entity_id, host_name)

        observed_category = placeholder.get(VertexProperties.CATEGORY)
        self.assertEqual(observed_category, EntityTypes.RESOURCE)

        is_placeholder = placeholder.get(VertexProperties.IS_PLACEHOLDER)
        self.assertEqual(is_placeholder, True)

    def test_key_values(self):

        LOG.debug('Test key values')

        host_name = 'host123456'
        observed_key_fields = HostTransformer()._key_values(
            [host_name]
        )

        self.assertEqual(EntityTypes.RESOURCE, observed_key_fields[0])
        self.assertEqual(
            nova_transformers.HOST_TYPE,
            observed_key_fields[1]
        )
        self.assertEqual(host_name, observed_key_fields[2])

    def test_extract_key(self):
        pass

    def test_snapshot_transform(self):
        LOG.debug('Nova host transformer test: transform entity event')

        # Test setup
        spec_list = mock_sync.simple_host_generators(
            zone_num=2,
            host_num=4,
            snapshot_events=5)

        host_events = mock_sync.generate_random_events_list(spec_list)

        for event in host_events:
            # Test action
            wrapper = HostTransformer().transform(event)

            # Test assertions
            self._validate_vertex_props(wrapper.vertex, event)

            neighbors = wrapper.neighbors
            self.assertEqual(1, len(neighbors))
            self._validate_zone_neighbor(neighbors[0], event)

            if SyncMode.SNAPSHOT == event['sync_mode']:
                self.assertEqual(EventAction.UPDATE, wrapper.action)
            else:
                self.assertEqual(EventAction.CREATE, wrapper.action)

    def _validate_zone_neighbor(self, zone, event):

        sync_mode = event['sync_mode']
        zone_name = tbase.extract_field_value(
            event,
            HostTransformer().ZONE_NAME[sync_mode]
        )
        time = tbase.extract_field_value(
            event,
            HostTransformer().TIMESTAMP[sync_mode]
        )

        zt = nova_transformers.ZoneTransformer()
        expected_neighbor = zt.create_placeholder_vertex(zone_name, time)
        self.assertEqual(expected_neighbor, zone.vertex)

        # Validate neighbor edge
        edge = zone.edge
        self.assertEqual(edge.source_id, zone.vertex.vertex_id)
        self.assertEqual(
            edge.target_id,
            HostTransformer().extract_key(event)
        )
        self.assertEqual(edge.label, EdgeLabels.CONTAINS)

    def _validate_vertex_props(self, vertex, event):

        sync_mode = event['sync_mode']
        extract_value = tbase.extract_field_value

        expected_id = extract_value(
            event,
            HostTransformer().HOST_NAME[sync_mode]
        )
        observed_id = vertex[VertexProperties.ID]
        self.assertEqual(expected_id, observed_id)
        self.assertEqual(
            EntityTypes.RESOURCE,
            vertex[VertexProperties.CATEGORY]
        )

        self.assertEqual(
            nova_transformers.HOST_TYPE,
            vertex[VertexProperties.TYPE]
        )

        expected_timestamp = extract_value(
            event,
            HostTransformer.TIMESTAMP[sync_mode]
        )
        observed_timestamp = vertex[VertexProperties.UPDATE_TIMESTAMP]
        self.assertEqual(expected_timestamp, observed_timestamp)

        expected_name = extract_value(
            event,
            HostTransformer.HOST_NAME[sync_mode]
        )
        observed_name = vertex[VertexProperties.NAME]
        self.assertEqual(expected_name, observed_name)

        is_placeholder = vertex[VertexProperties.IS_PLACEHOLDER]
        self.assertFalse(is_placeholder)

        is_deleted = vertex[VertexProperties.IS_DELETED]
        self.assertFalse(is_deleted)

    def test_extract_action_type(self):
        LOG.debug('Test extract action type')

        # Test setup
        spec_list = mock_sync.simple_host_generators(
            zone_num=1,
            host_num=1,
            snapshot_events=1,
            snap_vals={'sync_mode': SyncMode.SNAPSHOT})

        hosts_events = mock_sync.generate_random_events_list(spec_list)

        # Test action
        action = HostTransformer()._extract_action_type(hosts_events[0])

        # Test assertion
        self.assertEqual(EventAction.UPDATE, action)

        # Test setup
        spec_list = mock_sync.simple_host_generators(
            zone_num=1,
            host_num=1,
            snapshot_events=1,
            snap_vals={'sync_mode': SyncMode.INIT_SNAPSHOT})
        hosts_events = mock_sync.generate_random_events_list(spec_list)

        # Test action
        action = HostTransformer()._extract_action_type(hosts_events[0])

        # Test assertions
        self.assertEqual(EventAction.CREATE, action)

        # TODO(lhartal): To add extract action from update event
