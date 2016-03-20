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

from oslo_log import log as logging

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageTransformerError
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins import transformer_base

LOG = logging.getLogger(__name__)
NOVA_HOST = 'nova.host'


class StaticPhysicalTransformer(transformer_base.TransformerBase):

    RELATION_TYPE = 'relation_type'
    RELATIONSHIPS_SECTION = 'relationships'
    SWITCH = 'switch'

    def __init__(self, transformers):
        self.transformers = transformers
        self._register_relations_direction()

    def _create_entity_vertex(self, entity_event):
        sync_type = entity_event[VProps.TYPE]
        entity_id = entity_event[VProps.ID]
        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]
        update_timestamp = self._format_update_timestamp(None,
                                                         sample_timestamp)
        state = entity_event[VProps.STATE]
        entity_key = self.extract_key(entity_event)
        metadata = self._extract_metadata(entity_event)

        return graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=sync_type,
            update_timestamp=update_timestamp,
            sample_timestamp=sample_timestamp,
            entity_state=state,
            metadata=metadata)

    def _create_neighbors(self, entity_event):
        neighbors = []
        entity_type = entity_event[VProps.TYPE]
        entity_key = self.extract_key(entity_event)
        timestamp = entity_event[SyncProps.SAMPLE_DATE]

        for neighbor_details in entity_event[self.RELATIONSHIPS_SECTION]:
            # TODO(alexey): need to decide what to do if one of the entities
            #               fails
            neighbor = self._create_neighbor(neighbor_details, entity_type,
                                             entity_key, timestamp)
            if neighbor is not None:
                neighbors.append(neighbor)

        return neighbors

    def _create_neighbor(self, neighbor_details, entity_type,
                         entity_key, sample_timestamp):
        neighbor_type = neighbor_details[VProps.TYPE]
        entity_transformer = self.transformers[neighbor_type]

        if entity_transformer:
            neighbor_id = neighbor_details[VProps.ID]
            relation_type = neighbor_details[self.RELATION_TYPE]
            is_source = self._find_relation_direction_source(
                entity_type, neighbor_type)

            properties = {
                VProps.TYPE: neighbor_type,
                VProps.ID: neighbor_id,
                VProps.SAMPLE_TIMESTAMP: sample_timestamp
            }
            neighbor = entity_transformer.create_placeholder_vertex(
                **properties)

            relation_edge = graph_utils.create_edge(
                source_id=neighbor.vertex_id if is_source else entity_key,
                target_id=entity_key if is_source else neighbor.vertex_id,
                relationship_type=relation_type)

            return transformer_base.Neighbor(neighbor, relation_edge)
        else:
            LOG.warning('Cannot find zone transformer')
            return None

    def _extract_action_type(self, entity_event):
        sync_mode = entity_event[SyncProps.SYNC_MODE]

        if SyncMode.INIT_SNAPSHOT == sync_mode:
            return EventAction.CREATE_ENTITY

        if SyncMode.SNAPSHOT == sync_mode:
            return EventAction.UPDATE_ENTITY

        if SyncMode.UPDATE == sync_mode:
            if SyncProps.EVENT_TYPE in entity_event:
                event_type = entity_event[SyncProps.EVENT_TYPE]
                return EventAction.DELETE_ENTITY if event_type == EventAction.DELETE_ENTITY \
                    else EventAction.UPDATE_ENTITY
            else:
                return EventAction.UPDATE_ENTITY

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)

    def extract_key(self, entity_event):
        entity_id = entity_event[VProps.ID]
        sync_type = entity_event[VProps.TYPE]
        key_fields = self.key_values(sync_type, entity_id)
        return transformer_base.build_key(key_fields)

    def key_values(self, *args):
        return (EntityCategory.RESOURCE,) + args

    def create_placeholder_vertex(self, **kwargs):
        if VProps.TYPE not in kwargs:
            LOG.error("Can't create placeholder vertex. Missing property TYPE")
            raise ValueError('Missing property TYPE')

        if VProps.ID not in kwargs:
            LOG.error("Can't create placeholder vertex. Missing property ID")
            raise ValueError('Missing property ID')

        key_fields = self.key_values(kwargs[VProps.TYPE],
                                     kwargs[VProps.ID])

        return graph_utils.create_vertex(
            transformer_base.build_key(key_fields),
            entity_id=kwargs[VProps.ID],
            entity_category=EntityCategory.RESOURCE,
            entity_type=kwargs[VProps.TYPE],
            sample_timestamp=kwargs[VProps.SAMPLE_TIMESTAMP],
            is_placeholder=True)

    @staticmethod
    def _extract_metadata(entity_event):
        metadata = {VProps.NAME: entity_event[VProps.NAME]}
        return metadata

    def _find_relation_direction_source(self, entity_type, neighbor_type):
        # TODO(alexey): maybe check if this type exists, because it throws
        #               exception if it doesn't
        return self.relation_direction[(entity_type, neighbor_type)]

    def _register_relations_direction(self):
        self.relation_direction = {}

        relationship = (self.SWITCH, NOVA_HOST)
        self.relation_direction[relationship] = True

        relationship = (self.SWITCH, self.SWITCH)
        self.relation_direction[relationship] = True
