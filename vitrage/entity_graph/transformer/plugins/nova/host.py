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


class Compute(base.TransformerBase):

    HOST_TYPE = EntityType.NOVA_HOST

    # Fields returned from Nova Availability Zone snapshot
    HOST_NAME = {
        SyncMode.SNAPSHOT: ('_info', 'host_name',),
        SyncMode.INIT_SNAPSHOT: ('_info', 'host_name',)
    }

    ZONE_NAME = {
        SyncMode.SNAPSHOT: ('zone',),
        SyncMode.INIT_SNAPSHOT: ('zone',)
    }

    TIMESTAMP = {
        SyncMode.SNAPSHOT: (SyncProps.SAMPLE_DATE,),
        SyncMode.INIT_SNAPSHOT: (SyncProps.SAMPLE_DATE,)
    }

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[sync_mode]
        )
        metadata = {VertexProperties.NAME: host_name}

        entity_key = self.extract_key(entity_event)

        timestamp = extract_field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        return graph_utils.create_vertex(
            entity_key,
            entity_id=host_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.HOST_TYPE,
            update_timestamp=timestamp,
            metadata=metadata
        )

    def _create_neighbors(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        neighbors = []

        timestamp = extract_field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        zone_neighbor = self._create_zone_neighbor(
            entity_event,
            timestamp,
            self.extract_key(entity_event),
            self.ZONE_NAME[sync_mode]
        )

        if zone_neighbor is not None:
            neighbors.append(zone_neighbor)

        return neighbors

    def _create_zone_neighbor(
            self, entity_event, timestamp, host_vertex_id, zone_name_path):

        zone_transformer = self.transformers[EntityType.NOVA_ZONE]

        if zone_transformer:

            zone_name = extract_field_value(entity_event, zone_name_path)

            zone_neighbor = zone_transformer.create_placeholder_vertex(
                zone_name,
                timestamp
            )
            relation_edge = graph_utils.create_edge(
                source_id=zone_neighbor.vertex_id,
                target_id=host_vertex_id,
                relationship_type=EdgeLabels.CONTAINS
            )
            return base.Neighbor(zone_neighbor, relation_edge)
        else:
            LOG.warning('Cannot find zone transformer')

        return None

    def _key_values(self, mutable_fields):

        fixed_fields = [EntityCategory.RESOURCE, self.HOST_TYPE]
        return fixed_fields + mutable_fields

    def extract_key(self, entity_event):

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[entity_event[SyncProps.SYNC_MODE]]
        )

        key_fields = self._key_values([host_name])
        return base.build_key(key_fields)

    def create_placeholder_vertex(self, host_name, timestamp):

        key_fields = self._key_values([host_name])

        return graph_utils.create_vertex(
            base.build_key(key_fields),
            entity_id=host_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=self.HOST_TYPE,
            update_timestamp=timestamp,
            is_placeholder=True
        )
