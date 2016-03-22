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
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties as VProps
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins.base.resource.transformer import \
    BaseResourceTransformer
from vitrage.synchronizer.plugins import transformer_base
from vitrage.synchronizer.plugins.transformer_base import extract_field_value


LOG = logging.getLogger(__name__)
NOVA_HOST = 'nova.host'
NOVA_ZONE = 'nova.zone'


class ZoneTransformer(BaseResourceTransformer):

    ZONE_TYPE = NOVA_ZONE

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
            self.ZONE_NAME[sync_mode])

        metadata = {
            VProps.NAME: zone_name
        }

        entity_key = self._create_entity_key(entity_event)
        is_available = extract_field_value(
            entity_event,
            self.ZONE_STATE[sync_mode])
        state = self.STATE_AVAILABLE if is_available \
            else self.STATE_UNAVAILABLE

        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]

        update_timestamp = self._format_update_timestamp(None,
                                                         sample_timestamp)

        return graph_utils.create_vertex(
            entity_key,
            entity_id=zone_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.ZONE_TYPE,
            entity_state=state,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_neighbors(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        zone_vertex_id = self._create_entity_key(entity_event)

        neighbors = [self._create_node_neighbor(zone_vertex_id)]

        hosts = extract_field_value(entity_event, self.HOSTS[sync_mode])
        host_transformer = self.transformers[NOVA_HOST]

        if host_transformer:
            for key in hosts:

                host_available = extract_field_value(
                    hosts[key],
                    self.HOST_AVAILABLE[sync_mode])
                host_active = extract_field_value(
                    hosts[key],
                    self.HOST_ACTIVE[sync_mode])

                if host_available and host_active:
                    host_state = self.STATE_AVAILABLE
                else:
                    host_state = self.STATE_UNAVAILABLE

                host_neighbor = self._create_host_neighbor(
                    zone_vertex_id,
                    key,
                    host_state,
                    entity_event[SyncProps.SAMPLE_DATE])
                neighbors.append(host_neighbor)
        else:
            LOG.warning('Cannot find host transformer')

        return neighbors

    @staticmethod
    def _create_node_neighbor(zone_vertex_id):

        node_vertex = transformer_base.create_node_placeholder_vertex()

        relation_edge = graph_utils.create_edge(
            source_id=node_vertex.vertex_id,
            target_id=zone_vertex_id,
            relationship_type=EdgeLabels.CONTAINS)
        return transformer_base.Neighbor(node_vertex, relation_edge)

    def _create_host_neighbor(self, zone_id, host_name,
                              host_state, sample_timestamp):

        host_transformer = self.transformers['nova.host']

        properties = {
            VProps.ID: host_name,
            VProps.SAMPLE_TIMESTAMP: sample_timestamp,
            VProps.STATE: host_state
        }
        host_neighbor = \
            host_transformer.create_placeholder_vertex(**properties)

        relation_edge = graph_utils.create_edge(
            source_id=zone_id,
            target_id=host_neighbor.vertex_id,
            relationship_type=EdgeLabels.CONTAINS)

        return transformer_base.Neighbor(host_neighbor, relation_edge)

    def _create_entity_key(self, entity_event):

        zone_name = extract_field_value(
            entity_event,
            self.ZONE_NAME[entity_event[SyncProps.SYNC_MODE]])

        key_fields = self._key_values(self.ZONE_TYPE, zone_name)
        return transformer_base.build_key(key_fields)

    def create_placeholder_vertex(self, **kwargs):
        if VProps.ID not in kwargs:
            LOG.error('Cannot create placeholder vertex. Missing property ID')
            raise ValueError('Missing property ID')

        key = transformer_base.build_key(
            self._key_values(self.ZONE_TYPE, kwargs[VProps.ID]))

        return graph_utils.create_vertex(
            key,
            entity_id=kwargs[VProps.ID],
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.ZONE_TYPE,
            sample_timestamp=kwargs[VProps.SAMPLE_TIMESTAMP],
            is_placeholder=True)
