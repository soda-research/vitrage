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

from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EventAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.cinder.volume import CINDER_VOLUME_DATASOURCE
from vitrage.datasources.heat.stack import HEAT_STACK_DATASOURCE
from vitrage.datasources.neutron.network import NEUTRON_NETWORK_DATASOURCE
from vitrage.datasources.neutron.port import NEUTRON_PORT_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources.resource_transformer_base import \
    ResourceTransformerBase
from vitrage.datasources import transformer_base as tbase
from vitrage.datasources.transformer_base import build_key
from vitrage.datasources.transformer_base import extract_field_value
from vitrage.datasources.transformer_base import Neighbor
import vitrage.graph.utils as graph_utils


LOG = logging.getLogger(__name__)


class HeatStackTransformer(ResourceTransformerBase):

    RESOURCE_TYPE_CONVERSION = {
        'OS::Nova::Server': NOVA_INSTANCE_DATASOURCE,
        'OS::Cinder::Volume': CINDER_VOLUME_DATASOURCE,
        'OS::Neutron::Net': NEUTRON_NETWORK_DATASOURCE,
        'OS::Neutron::Port': NEUTRON_PORT_DATASOURCE
    }

    # Event types which need to refer them differently
    UPDATE_EVENT_TYPES = {
        'orchestration.stack.delete.end': EventAction.DELETE_ENTITY,
    }

    def __init__(self, transformers, conf):
        super(HeatStackTransformer, self).__init__(transformers, conf)

    def _create_snapshot_entity_vertex(self, entity_event):
        stack_name = extract_field_value(entity_event, 'stack_name')
        stack_id = extract_field_value(entity_event, 'id')
        stack_state = extract_field_value(entity_event, 'stack_status')
        timestamp = extract_field_value(entity_event, 'creation_time')
        project_id = extract_field_value(entity_event, 'project_id')

        return self._create_vertex(entity_event,
                                   stack_name,
                                   stack_id,
                                   stack_state,
                                   timestamp,
                                   project_id)

    def _create_update_entity_vertex(self, entity_event):

        volume_name = extract_field_value(entity_event, 'stack_name')
        volume_id = extract_field_value(entity_event, 'stack_identity')
        volume_state = extract_field_value(entity_event, 'state')
        timestamp = entity_event.get('create_at', None)
        project_id = entity_event.get('tenant_id', None)

        return self._create_vertex(entity_event,
                                   volume_name,
                                   volume_id,
                                   volume_state,
                                   timestamp,
                                   project_id)

    def _create_vertex(self,
                       entity_event,
                       stack_name,
                       stack_id,
                       stack_state,
                       update_timestamp,
                       project_id):
        metadata = {
            VProps.NAME: stack_name,
            VProps.PROJECT_ID: project_id,
        }

        entity_key = self._create_entity_key(entity_event)

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        return graph_utils.create_vertex(
            entity_key,
            entity_id=stack_id,
            entity_category=EntityCategory.RESOURCE,
            entity_type=HEAT_STACK_DATASOURCE,
            entity_state=stack_state,
            sample_timestamp=sample_timestamp,
            update_timestamp=update_timestamp,
            metadata=metadata)

    def _create_snapshot_neighbors(self, entity_event):
        return self._create_neighbors(entity_event)

    def _create_update_neighbors(self, entity_event):
        return self._create_neighbors(entity_event)

    def _create_entity_key(self, entity_event):

        is_update_event = tbase.is_update_event(entity_event)
        id_field_path = 'stack_identity' if is_update_event else 'id'
        volume_id = extract_field_value(entity_event, id_field_path)

        key_fields = self._key_values(HEAT_STACK_DATASOURCE, volume_id)
        return build_key(key_fields)

    def _create_neighbors(self, entity_event):
        return [self._create_neighbor(entity_event, neighbor)
                for neighbor in entity_event['resources']]

    def _create_neighbor(self,
                         entity_event,
                         neighbor):
        datasource_type = \
            self.RESOURCE_TYPE_CONVERSION[neighbor['resource_type']]
        transformer = self.transformers.get(datasource_type, None)

        stack_vitrage_id = self._create_entity_key(entity_event)

        neighbor_id = neighbor['physical_resource_id']

        sample_timestamp = entity_event[DSProps.SAMPLE_DATE]

        properties = {
            VProps.ID: neighbor_id,
            VProps.TYPE: datasource_type,
            VProps.SAMPLE_TIMESTAMP: sample_timestamp
        }
        instance_vertex = transformer.create_placeholder_vertex(**properties)

        relationship_edge = graph_utils.create_edge(
            source_id=stack_vitrage_id,
            target_id=instance_vertex.vertex_id,
            relationship_type=EdgeLabel.COMPRISED)

        return Neighbor(instance_vertex, relationship_edge)

    def get_type(self):
        return HEAT_STACK_DATASOURCE
