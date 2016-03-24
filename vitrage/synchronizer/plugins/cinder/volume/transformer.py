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
from vitrage.common.constants import EventAction
from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageTransformerError
import vitrage.graph.utils as graph_utils
from vitrage.synchronizer.plugins.base.resource.transformer import \
    BaseResourceTransformer
from vitrage.synchronizer.plugins.cinder.volume import CINDER_VOLUME_PLUGIN
from vitrage.synchronizer.plugins.nova.instance import NOVA_INSTANCE_PLUGIN
from vitrage.synchronizer.plugins import transformer_base
from vitrage.synchronizer.plugins.transformer_base import extract_field_value


LOG = logging.getLogger(__name__)


class CinderVolumeTransformer(BaseResourceTransformer):

    # Fields returned from Nova Instance snapshot
    VOLUME_ID = {
        SyncMode.SNAPSHOT: ('id',),
        SyncMode.INIT_SNAPSHOT: ('id',),
        SyncMode.UPDATE: ('payload', 'instance_id')
    }

    VOLUME_STATE = {
        SyncMode.SNAPSHOT: ('status',),
        SyncMode.INIT_SNAPSHOT: ('status',),
        SyncMode.UPDATE: ('payload', 'state')
    }

    VOLUME_UPDATE_TIMESTAMP = {
        SyncMode.SNAPSHOT: ('created_at',),
        SyncMode.INIT_SNAPSHOT: ('created_at',),
        SyncMode.UPDATE: ('metadata', 'timestamp')
    }

    VOLUME_NAME = {
        SyncMode.SNAPSHOT: ('display_name',),
        SyncMode.INIT_SNAPSHOT: ('display_name',),
        SyncMode.UPDATE: ('payload', 'hostname')
    }

    # Event types which need to refer them differently
    EVENT_TYPES = {
        'compute.instance.delete.end': EventAction.DELETE_ENTITY,
        'compute.instance.create.start': EventAction.CREATE_ENTITY
    }

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, entity_event):
        sync_mode = entity_event[SyncProps.SYNC_MODE]

        metadata = {
            VProps.NAME: extract_field_value(entity_event,
                                             self.VOLUME_NAME[sync_mode])
        }

        entity_key = self._create_entity_key(entity_event)

        entity_id = extract_field_value(
            entity_event,
            self.VOLUME_ID[sync_mode])

        state = extract_field_value(
            entity_event,
            self.VOLUME_STATE[sync_mode])

        update_timestamp = extract_field_value(
            entity_event,
            self.VOLUME_UPDATE_TIMESTAMP[sync_mode])

        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]

        update_timestamp = self._format_update_timestamp(update_timestamp,
                                                         sample_timestamp)

        return graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=CINDER_VOLUME_PLUGIN,
            entity_state=state,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_neighbors(self, entity_event):
        return self._create_instance_neighbors(entity_event)

    def _extract_action_type(self, entity_event):
        sync_mode = entity_event[SyncProps.SYNC_MODE]

        if SyncMode.INIT_SNAPSHOT == sync_mode:
            return EventAction.CREATE_ENTITY

        if SyncMode.SNAPSHOT == sync_mode:
            return EventAction.UPDATE_ENTITY

        if SyncMode.UPDATE == sync_mode:
            return self.EVENT_TYPES.get(
                entity_event[self.UPDATE_EVENT_TYPE],
                EventAction.UPDATE_ENTITY)

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)

    def _create_entity_key(self, entity_event):

        volume_id = extract_field_value(
            entity_event,
            self.VOLUME_ID[entity_event[SyncProps.SYNC_MODE]])

        key_fields = self._key_values(CINDER_VOLUME_PLUGIN, volume_id)
        return transformer_base.build_key(key_fields)

    def create_placeholder_vertex(self, **kwargs):
        if VProps.ID not in kwargs:
            LOG.error('Cannot create placeholder vertex. Missing property ID')
            raise ValueError('Missing property ID')

        key_fields = self._key_values(CINDER_VOLUME_PLUGIN, kwargs[VProps.ID])

        return graph_utils.create_vertex(
            transformer_base.build_key(key_fields),
            entity_id=kwargs[VProps.ID],
            entity_category=EntityCategory.RESOURCE,
            entity_type=CINDER_VOLUME_PLUGIN,
            sample_timestamp=kwargs[VProps.SAMPLE_TIMESTAMP],
            is_placeholder=True)

    def _create_instance_neighbors(self, entity_event):
        transformer = self.transformers[NOVA_INSTANCE_PLUGIN]

        if transformer:
            return [self._create_instance_neighbor(entity_event,
                                                   attachment,
                                                   transformer)
                    for attachment in entity_event['attachments']]
        else:
            LOG.warning('Cannot find instance transformer')

    def _create_instance_neighbor(self,
                                  entity_event,
                                  attachment,
                                  instance_transformer):
        volume_vitrage_id = self._create_entity_key(entity_event)

        instance_id = attachment['server_id']

        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]

        properties = {
            VProps.ID: instance_id,
            VProps.SAMPLE_TIMESTAMP: sample_timestamp
        }
        instance_vertex = \
            instance_transformer.create_placeholder_vertex(
                **properties)

        relationship_edge = graph_utils.create_edge(
            source_id=volume_vitrage_id,
            target_id=instance_vertex.vertex_id,
            relationship_type=EdgeLabels.ATTACHED)

        return transformer_base.Neighbor(instance_vertex, relationship_edge)
