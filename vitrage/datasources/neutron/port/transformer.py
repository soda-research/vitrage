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

from vitrage.datasources.resource_transformer_base import \
    ResourceTransformerBase

from oslo_log import log as logging

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.neutron.network import NEUTRON_NETWORK_DATASOURCE
from vitrage.datasources.neutron.port import NEUTRON_PORT_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import transformer_base as tbase
from vitrage.datasources.transformer_base import extract_field_value
from vitrage.datasources.transformer_base import Neighbor

import vitrage.graph.utils as graph_utils

LOG = logging.getLogger(__name__)


class PortTransformer(ResourceTransformerBase):

    # Event types which need to refer them differently
    UPDATE_EVENT_TYPES = {
        'port.delete.end': EventAction.DELETE_ENTITY,
    }

    def __init__(self, transformers):
        super(PortTransformer, self).__init__(transformers)

    def _create_entity_key(self, entity_event):
        key_fields = self._key_values(NEUTRON_PORT_DATASOURCE,
                                      extract_field_value(entity_event, 'id'))
        return tbase.build_key(key_fields)

    def _create_snapshot_entity_vertex(self, entity_event):
        name = extract_field_value(entity_event, 'name')
        entity_id = extract_field_value(entity_event, 'id')
        state = extract_field_value(entity_event, 'status')

        return self._create_vertex(entity_event, name if name else None,
                                   entity_id, state)

    def _create_vertex(self, entity_event, name, entity_id, state):

        metadata = {
            VProps.NAME: name,
        }

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        # TODO(Alexey): need to check here that only the UPDATE sync_mode will
        #               update the UPDATE_TIMESTAMP property
        update_timestamp = self._format_update_timestamp(
            extract_field_value(entity_event, DSProps.SAMPLE_DATE),
            sample_timestamp)

        return graph_utils.create_vertex(
            self._create_entity_key(entity_event),
            entity_id=entity_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=NEUTRON_PORT_DATASOURCE,
            entity_state=state,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_update_entity_vertex(self, entity_event):
        pass

    def _create_neighbors(self, entity_event):
        if tbase.is_update_event(entity_event):
            device_owner_property = 'device_owner'
            device_id_property = 'server_uuid'
            net_id_property = 'network_id'
        else:
            device_owner_property = 'device_owner'
            device_id_property = 'device_id'
            net_id_property = 'network_id'

        return self._create_port_neighbors(entity_event,
                                           device_owner_property,
                                           device_id_property,
                                           net_id_property)

    def _create_port_neighbors(self,
                               entity_event,
                               device_owner_property,
                               device_id_property,
                               net_id_property):

        instance = None
        net = self._create_net_neighbor(entity_event,
                                        net_id_property)

        if entity_event[device_owner_property] == 'compute:nova':
            instance = self._create_instance_neighbor(
                entity_event,
                device_id_property)

        return [net, instance] if instance else [net]

    def _create_instance_neighbor(self,
                                  entity_event,
                                  instance_id_property):
        port_vitrage_id = self._create_entity_key(entity_event)

        instance_id = entity_event[instance_id_property]

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        properties = {
            VProps.ID: instance_id,
            VProps.TYPE: NOVA_INSTANCE_DATASOURCE,
            VProps.SAMPLE_TIMESTAMP: sample_timestamp
        }
        instance_vertex = self.create_placeholder_vertex(**properties)

        relationship_edge = graph_utils.create_edge(
            source_id=port_vitrage_id,
            target_id=instance_vertex.vertex_id,
            relationship_type=EdgeLabels.ATTACHED)

        return Neighbor(instance_vertex, relationship_edge)

    def _create_net_neighbor(self, entity_event, net_id_property):
        port_vitrage_id = self._create_entity_key(entity_event)

        net_id = entity_event[net_id_property]

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        properties = {
            VProps.ID: net_id,
            VProps.TYPE: NEUTRON_NETWORK_DATASOURCE,
            VProps.SAMPLE_TIMESTAMP: sample_timestamp
        }

        net_vertex = self.create_placeholder_vertex(**properties)

        relationship_edge = graph_utils.create_edge(
            source_id=net_vertex.vertex_id,
            target_id=port_vitrage_id,
            relationship_type=EdgeLabels.CONTAINS)

        return Neighbor(net_vertex, relationship_edge)
