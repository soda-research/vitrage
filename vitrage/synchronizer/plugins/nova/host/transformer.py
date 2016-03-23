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
from vitrage.synchronizer.plugins.nova.host import NOVA_HOST_PLUGIN
from vitrage.synchronizer.plugins.nova.zone import NOVA_ZONE_PLUGIN
from vitrage.synchronizer.plugins import transformer_base
from vitrage.synchronizer.plugins.transformer_base import extract_field_value


LOG = logging.getLogger(__name__)


class HostTransformer(BaseResourceTransformer):

    # Fields returned from Nova Availability Zone snapshot
    HOST_NAME = {
        SyncMode.SNAPSHOT: ('_info', 'host_name',),
        SyncMode.INIT_SNAPSHOT: ('_info', 'host_name',)
    }

    ZONE_NAME = {
        SyncMode.SNAPSHOT: ('zone',),
        SyncMode.INIT_SNAPSHOT: ('zone',)
    }

    def __init__(self, transformers):
        self.transformers = transformers

    def _create_entity_vertex(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[sync_mode])
        metadata = {VProps.NAME: host_name}

        entity_key = self._create_entity_key(entity_event)

        sample_timestamp = entity_event[SyncProps.SAMPLE_DATE]

        update_timestamp = self._format_update_timestamp(None,
                                                         sample_timestamp)

        return graph_utils.create_vertex(
            entity_key,
            entity_id=host_name,
            entity_category=EntityCategory.RESOURCE,
            entity_type=NOVA_HOST_PLUGIN,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_neighbors(self, entity_event):

        sync_mode = entity_event[SyncProps.SYNC_MODE]

        neighbors = []

        zone_neighbor = self._create_zone_neighbor(
            entity_event,
            entity_event[SyncProps.SAMPLE_DATE],
            self._create_entity_key(entity_event),
            self.ZONE_NAME[sync_mode])

        if zone_neighbor is not None:
            neighbors.append(zone_neighbor)

        return neighbors

    def _create_zone_neighbor(self,
                              entity_event,
                              sample_timestamp,
                              host_vertex_id,
                              zone_name_path):

        zone_transformer = self.transformers[NOVA_ZONE_PLUGIN]

        if zone_transformer:

            zone_name = extract_field_value(entity_event, zone_name_path)

            properties = {
                VProps.ID: zone_name,
                VProps.SAMPLE_TIMESTAMP: sample_timestamp
            }
            zone_neighbor = zone_transformer.create_placeholder_vertex(
                **properties)
            relation_edge = graph_utils.create_edge(
                source_id=zone_neighbor.vertex_id,
                target_id=host_vertex_id,
                relationship_type=EdgeLabels.CONTAINS)
            return transformer_base.Neighbor(zone_neighbor, relation_edge)
        else:
            LOG.warning('Cannot find zone transformer')

        return None

    def _create_entity_key(self, entity_event):

        host_name = extract_field_value(
            entity_event,
            self.HOST_NAME[entity_event[SyncProps.SYNC_MODE]])

        key_fields = self._key_values(NOVA_HOST_PLUGIN, host_name)
        return transformer_base.build_key(key_fields)

    def create_placeholder_vertex(self, **kwargs):
        if VProps.ID not in kwargs:
            LOG.error('Cannot create placeholder vertex. Missing property ID')
            raise ValueError('Missing property ID')

        key_fields = self._key_values(NOVA_HOST_PLUGIN, kwargs[VProps.ID])

        return graph_utils.create_vertex(
            transformer_base.build_key(key_fields),
            entity_id=kwargs[VProps.ID],
            entity_category=EntityCategory.RESOURCE,
            entity_type=NOVA_HOST_PLUGIN,
            sample_timestamp=kwargs[VProps.SAMPLE_TIMESTAMP],
            is_placeholder=True,
            entity_state=kwargs[VProps.STATE]
            if VProps.STATE in kwargs else None)
