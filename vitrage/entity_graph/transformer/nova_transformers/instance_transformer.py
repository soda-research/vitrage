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
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.common.exception import VitrageTransformerError
from vitrage.entity_graph.transformer import base
from vitrage.entity_graph.transformer.base import extract_field_value
import vitrage.graph.utils as graph_utils


LOG = logging.getLogger(__name__)


class InstanceTransformer(base.TransformerBase):

    INSTANCE_TYPE = EntityType.NOVA_INSTANCE

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
        SyncMode.SNAPSHOT: (SyncProps.SAMPLE_DATE,),
        SyncMode.INIT_SNAPSHOT: (SyncProps.SAMPLE_DATE,),
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

    UPDATE_EVENT_TYPE = SyncProps.EVENT_TYPE

    # Event types which need to refer them differently
    EVENT_TYPES = {
        'compute.instance.delete.end': EventAction.DELETE,
        'compute.instance.create.start': EventAction.CREATE
    }

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

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

        return graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.INSTANCE_TYPE,
            entity_project=project,
            entity_state=state,
            update_timestamp=update_timestamp,
            metadata=metadata
        )

    def _create_neighbors(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        neighbors = []
        host_transformer = self.transformers[EntityType.NOVA_HOST]

        if host_transformer:

            update_timestamp = extract_field_value(
                entity_event,
                self.TIMESTAMP[sync_mode]
            )

            host_neighbor = self._create_host_neighbor(
                self.extract_key(entity_event),
                extract_field_value(entity_event, self.HOST_NAME[sync_mode]),
                update_timestamp,
                host_transformer
            )
            neighbors.append(host_neighbor)
        else:
            LOG.warning('Cannot find host transformer')

        return neighbors

    def _extract_action_type(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

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
            self.INSTANCE_ID[entity_event[SyncProps.SYNC_MODE]])

        key_fields = self._key_values([instance_id])
        return base.build_key(key_fields)

    def _create_host_neighbor(
            self,
            vertex_id,
            host_name,
            timestamp,
            host_transformer
    ):

        host_vertex = host_transformer.create_placeholder_vertex(
            host_name,
            timestamp
        )

        relation_edge = graph_utils.create_edge(
            source_id=host_vertex.vertex_id,
            target_id=vertex_id,
            relationship_type=EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    def create_placeholder_vertex(self, instance_id, timestamp):

        key_fields = self._key_values([instance_id])

        return graph_utils.create_vertex(
            base.build_key(key_fields),
            entity_id=instance_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.INSTANCE_TYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )

    def _key_values(self, mutable_fields):
        return [EntityCategory.RESOURCE, self.INSTANCE_TYPE] + mutable_fields
