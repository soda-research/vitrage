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

from oslo_log import log as logging

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.transformer import base
from vitrage.entity_graph.transformer.base import extract_field_value
import vitrage.graph.utils as graph_utils


LOG = logging.getLogger(__name__)


class ZoneTransformer(base.TransformerBase):

    ZONE_TYPE = EntityType.NOVA_ZONE

    STATE_AVAILABLE = 'available'
    STATE_UNAVAILABLE = 'unavailable'

    # Fields returned from Nova Availability Zone snapshot
    ZONE_NAME = {
        SyncMode.SNAPSHOT: ('zoneName',),
        SyncMode.INIT_SNAPSHOT: ('zoneName',)
    }

    ZONE_STATE = {
        SyncMode.SNAPSHOT: ('zoneState', 'available',),
        SyncMode.INIT_SNAPSHOT: ('zoneState', 'available',)
    }

    TIMESTAMP = {
        SyncMode.SNAPSHOT: (SyncProps.SAMPLE_DATE,),
        SyncMode.INIT_SNAPSHOT: (SyncProps.SAMPLE_DATE,)
    }

    HOSTS = {
        SyncMode.SNAPSHOT: ('hosts',),
        SyncMode.INIT_SNAPSHOT: ('hosts',)
    }

    HOST_ACTIVE = {
        # The path is relative to specific host and not the whole event
        SyncMode.SNAPSHOT: ('nova-compute', 'active',),
        SyncMode.INIT_SNAPSHOT: ('nova-compute', 'active',)
    }

    HOST_AVAILABLE = {
        # The path is relative to specific host and not the whole event
        SyncMode.SNAPSHOT: ('nova-compute', 'available',),
        SyncMode.INIT_SNAPSHOT: ('nova-compute', 'available',)
    }

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        zone_name = extract_field_value(
            entity_event,
            self.ZONE_NAME[sync_mode]
        )

        metadata = {
            VertexProperties.NAME: zone_name
        }

        entity_key = self.extract_key(entity_event)
        is_available = extract_field_value(
            entity_event,
            self.ZONE_STATE[sync_mode]
        )
        state = self.STATE_AVAILABLE if is_available \
            else self.STATE_UNAVAILABLE

        timestamp = extract_field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        return graph_utils.create_vertex(
            entity_key,
            entity_id=zone_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.ZONE_TYPE,
            entity_state=state,
            update_timestamp=timestamp,
            metadata=metadata
        )

    def _create_neighbors(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        zone_vertex_id = self.extract_key(entity_event)

        neighbors = [self._create_node_neighbor(zone_vertex_id)]

        hosts = extract_field_value(entity_event, self.HOSTS[sync_mode])
        host_transformer = self.transformers[EntityType.NOVA_HOST]

        if host_transformer:

            timestamp = extract_field_value(
                entity_event,
                self.TIMESTAMP[sync_mode]
            )

            for key in hosts:

                host_available = extract_field_value(
                    hosts[key],
                    self.HOST_AVAILABLE[sync_mode]
                )
                host_active = extract_field_value(
                    hosts[key],
                    self.HOST_ACTIVE[sync_mode]
                )

                if host_available and host_active:
                    host_state = self.STATE_AVAILABLE
                else:
                    host_state = self.STATE_UNAVAILABLE

                host_neighbor = self._create_host_neighbor(
                    zone_vertex_id,
                    key,
                    host_state,
                    timestamp
                )
                neighbors.append(host_neighbor)
        else:
            LOG.warning('Cannot find host transformer')

        return neighbors

    def _create_node_neighbor(self, zone_vertex_id):

        node_vertex = base.create_node_placeholder_vertex()

        relation_edge = graph_utils.create_edge(
            source_id=node_vertex.vertex_id,
            target_id=zone_vertex_id,
            relationship_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(node_vertex, relation_edge)

    def _create_host_neighbor(self, zone_id, host_name, host_state, timestamp):

        host_transformer = self.transformers['nova.host']

        host_vertex = graph_utils.create_vertex(
            base.build_key(host_transformer._key_values([host_name])),
            entity_id=host_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.ZONE_TYPE,
            entity_state=host_state,
            update_timestamp=timestamp,
        )

        relation_edge = graph_utils.create_edge(
            source_id=zone_id,
            target_id=host_vertex.vertex_id,
            relationship_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    def extract_key(self, entity_event):

        zone_name = extract_field_value(
            entity_event,
            self.ZONE_NAME[entity_event[SyncProps.SYNC_MODE]]
        )

        key_fields = self._key_values([zone_name])
        return base.build_key(key_fields)

    def _key_values(self, mutable_fields):

        fixed_fields = [EntityCategory.RESOURCE, self.ZONE_TYPE]
        return fixed_fields + mutable_fields

    def create_placeholder_vertex(self, zone_name, timestamp):
        key = base.build_key(self._key_values([zone_name]))

        return graph_utils.create_vertex(
            key,
            entity_id=zone_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.ZONE_TYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )
