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
from vitrage.common.constants import EntityTypes
from vitrage.common.constants import EventAction
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.common.exception import VitrageTransformerError
from vitrage.entity_graph.transformer import base
from vitrage.entity_graph.transformer.base import extract_field_value
import vitrage.graph.utils as graph_utils


LOG = logging.getLogger(__name__)


INSTANCE_SUBTYPE = 'nova.instance'
HOST_SUBTYPE = 'nova.host'
ZONE_SUBTYPE = 'nova.zone'


class InstanceTransformer(base.TransformerBase):

    # Fields returned from Nova Instance snapshot
    INSTANCE_ID = {
        SyncMode.SNAPSHOT: ('id',),
        SyncMode.INIT_SNAPSHOT: ('id',),
        SyncMode.UPDATE: ('payload', 'instance_id')
    }

    INSTANCE_STATE = {
        SyncMode.SNAPSHOT: ('status',),
        SyncMode.INIT_SNAPSHOT: ('status',),
        SyncMode.UPDATE: ('payload', 'state')
    }

    TIMESTAMP = {
        SyncMode.SNAPSHOT: ('sample_date',),
        SyncMode.INIT_SNAPSHOT: ('sample_date',),
        SyncMode.UPDATE: ('metadata', 'timestamp')
    }

    HOST_NAME = {
        SyncMode.SNAPSHOT: ('OS-EXT-SRV-ATTR:host',),
        SyncMode.INIT_SNAPSHOT: ('OS-EXT-SRV-ATTR:host',),
        SyncMode.UPDATE: ('payload', 'host')
    }

    PROJECT_ID = {
        SyncMode.SNAPSHOT: ('tenant_id',),
        SyncMode.INIT_SNAPSHOT: ('tenant_id',),
        SyncMode.UPDATE: ('payload', 'tenant_id')
    }

    INSTANCE_NAME = {
        SyncMode.SNAPSHOT: ('name',),
        SyncMode.INIT_SNAPSHOT: ('name',),
        SyncMode.UPDATE: ('payload', 'hostname')
    }

    UPDATE_EVENT_TYPE = 'event_type'

    # Event types which need to refer them differently
    EVENT_TYPES = {
        'compute.instance.delete.end': EventAction.DELETE,
        'compute.instance.create.start': EventAction.CREATE
    }

    def transform(self, entity_event):
        sync_mode = entity_event['sync_mode']

        metadata = {
            VertexProperties.NAME: extract_field_value(
                entity_event,
                self.INSTANCE_NAME[sync_mode]
            ),
            VertexProperties.IS_PLACEHOLDER: False
        }

        entity_key = self.extract_key(entity_event)

        entity_id = extract_field_value(
            entity_event,
            self.INSTANCE_ID[sync_mode]
        )
        project = extract_field_value(entity_event, self.PROJECT_ID[sync_mode])
        state = extract_field_value(
            entity_event,
            self.INSTANCE_STATE[sync_mode]
        )
        update_timestamp = extract_field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        entity_vertex = graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            entity_project=project,
            entity_state=state,
            update_timestamp=update_timestamp,
            metadata=metadata
        )

        host_neighbor = self.create_host_neighbor(
            entity_vertex.vertex_id,
            extract_field_value(entity_event, self.HOST_NAME[sync_mode]),
            update_timestamp
        )

        return base.EntityWrapper(
            entity_vertex,
            [host_neighbor],
            self._extract_action_type(entity_event))

    def _extract_action_type(self, entity_event):

        sync_mode = entity_event['sync_mode']

        if SyncMode.UPDATE == sync_mode:
            return self.EVENT_TYPES.get(
                entity_event[self.UPDATE_EVENT_TYPE],
                EventAction.UPDATE)

        if SyncMode.SNAPSHOT == sync_mode:
            return EventAction.UPDATE

        if SyncMode.INIT_SNAPSHOT == sync_mode:
            return EventAction.CREATE

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)

    def extract_key(self, entity_event):

        instance_id = extract_field_value(
            entity_event,
            self.INSTANCE_ID[entity_event['sync_mode']])

        key_fields = self._key_values([instance_id])
        return base.build_key(key_fields)

    def create_host_neighbor(self, vertex_id, host_name, timestamp):

        ht = HostTransformer()
        host_vertex = ht.create_placeholder_vertex(host_name, timestamp)

        relation_edge = graph_utils.create_edge(
            source_id=host_vertex.vertex_id,
            target_id=vertex_id,
            relation_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    def create_placeholder_vertex(self, instance_id, timestamp):

        key_fields = self._key_values([instance_id])

        return graph_utils.create_vertex(
            base.build_key(key_fields),
            entity_id=instance_id,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )

    def _key_values(self, mutable_fields):
        return [EntityTypes.RESOURCE, INSTANCE_SUBTYPE] + mutable_fields


class HostTransformer(base.TransformerBase):

    # Fields returned from Nova Availability Zone snapshot
    HOST_NAME = {
        SyncMode.SNAPSHOT: ('host_name',),
        SyncMode.INIT_SNAPSHOT: ('host_name',)
    }

    ZONE_NAME = {
        SyncMode.SNAPSHOT: ('zone',),
        SyncMode.INIT_SNAPSHOT: ('zone',)
    }

    TIMESTAMP = {
        SyncMode.SNAPSHOT: ('sample_date',),
        SyncMode.INIT_SNAPSHOT: ('sample_date',)
    }

    def transform(self, entity_event):

        sync_mode = entity_event['sync_mode']

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[sync_mode]
        )
        metadata = {
            VertexProperties.NAME: host_name
        }
        entity_key = self.extract_key(entity_event)

        timestamp = extract_field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        entity_vertex = graph_utils.create_vertex(
            entity_key,
            entity_id=host_name,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=HOST_SUBTYPE,
            update_timestamp=timestamp,
            metadata=metadata
        )

        zone_name = extract_field_value(
            entity_event,
            self.ZONE_NAME[sync_mode]
        )
        zone_neighbor = self.create_zone_neighbor(
            zone_name,
            timestamp,
            entity_key
        )

        return base.EntityWrapper(
            entity_vertex,
            [zone_neighbor],
            self._extract_action_type(entity_event))

    def create_zone_neighbor(self, zone_name, timestamp, host_vertex_id):

        zone_neighbor = ZoneTransformer().create_placeholder_vertex(
            zone_name,
            timestamp
        )
        relation_edge = graph_utils.create_edge(
            source_id=zone_neighbor.vertex_id,
            target_id=host_vertex_id,
            relation_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(zone_neighbor, relation_edge)

    def _key_values(self, mutable_fields):

        fixed_fields = [EntityTypes.RESOURCE, HOST_SUBTYPE]
        return fixed_fields + mutable_fields

    def extract_key(self, entity_event):

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[entity_event['sync_mode']]
        )

        key_fields = self._key_values([host_name])
        return base.build_key(key_fields)

    def create_placeholder_vertex(self, host_name, timestamp):

        key_fields = self._key_values([host_name])

        return graph_utils.create_vertex(
            base.build_key(key_fields),
            entity_id=host_name,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=HOST_SUBTYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )


class ZoneTransformer(base.TransformerBase):

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
        SyncMode.SNAPSHOT: ('sample_date',),
        SyncMode.INIT_SNAPSHOT: ('sample_date',)
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

    def transform(self, entity_event):
        sync_mode = entity_event['sync_mode']

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

        entity_vertex = graph_utils.create_vertex(
            entity_key,
            entity_id=zone_name,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=ZONE_SUBTYPE,
            entity_state=state,
            update_timestamp=timestamp,
            metadata=metadata
        )

        neighbors = [self._create_node_neighbor(entity_vertex)]

        hosts = extract_field_value(entity_event, self.HOSTS[sync_mode])

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
                entity_vertex.vertex_id,
                key,
                host_state,
                timestamp
            )
            neighbors.append(host_neighbor)

        return base.EntityWrapper(
            entity_vertex,
            neighbors,
            self._extract_action_type(entity_event))

    def _create_node_neighbor(self, zone_vertex):

        node_vertex = base.create_node_placeholder_vertex()

        relation_edge = graph_utils.create_edge(
            source_id=node_vertex.vertex_id,
            target_id=zone_vertex.vertex_id,
            relation_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(node_vertex, relation_edge)

    def _create_host_neighbor(self, zone_id, host_name, host_state, timestamp):

        host_vertex = graph_utils.create_vertex(
            base.build_key(HostTransformer()._key_values([host_name])),
            entity_id=host_name,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=ZONE_SUBTYPE,
            entity_state=host_state,
            update_timestamp=timestamp,
        )

        relation_edge = graph_utils.create_edge(
            source_id=zone_id,
            target_id=host_vertex.vertex_id,
            relation_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    def extract_key(self, entity_event):

        zone_name = extract_field_value(
            entity_event,
            self.ZONE_NAME[entity_event['sync_mode']]
        )

        key_fields = self._key_values([zone_name])
        return base.build_key(key_fields)

    def _key_values(self, mutable_fields):

        fixed_fields = [EntityTypes.RESOURCE, ZONE_SUBTYPE]
        return fixed_fields + mutable_fields

    def create_placeholder_vertex(self, zone_name, timestamp):
        key = base.build_key(self._key_values([zone_name]))

        return graph_utils.create_vertex(
            key,
            entity_id=zone_name,
            entity_type=EntityTypes.RESOURCE,
            entity_subtype=ZONE_SUBTYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )
