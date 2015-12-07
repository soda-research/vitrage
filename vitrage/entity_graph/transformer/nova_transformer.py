# Copyright 2015 - Alcatel-Lucent
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

import vitrage.common.constants as cons
from vitrage.entity_graph.transformer import base
import vitrage.graph.utils as graph_utils

LOG = logging.getLogger(__name__)

INSTANCE_SUBTYPE = 'nova.instance'
HOST_SUBTYPE = 'nova.host'


class InstanceTransformer(base.Transformer):

    # # Fields returned from Nova Instance snapshot
    SNAPSHOT_INSTANCE_ID = 'id'
    UPDATE_INSTANCE_ID = 'instance_id'

    SNAPSHOT_INSTANCE_STATE = 'status'
    UPDATE_INSTANCE_STATE = 'state'

    SNAPSHOT_TIMESTAMP = 'updated'
    UPDATE_TIMESTAMP = 'metadata;timestamp'

    PROJECT_ID = 'tenant_id'
    INSTANCE_NAME = 'name'
    HOST_NAME = 'OS-EXT-SRV-ATTR:host'

    def __init__(self):

        self.transform_methods = {
            cons.SyncMode.SNAPSHOT: self._transform_snapshot_event,
            cons.SyncMode.INIT_SNAPSHOT: self._transform_init_snapshot_event,
            cons.SyncMode.UPDATE: self._transform_update_event
        }

    def transform(self, entity_event):
        """Transform an entity event into entity wrapper.

        Entity event is received from synchronizer it need to be
        transformed into entity wrapper. The wrapper contains:
            1. Entity Vertex - The vertex itself with all fields
            2. Neighbor list - neighbor vertex with partial data and an edge
            3. Action type - CREATE/UPDATE/DELETE

        :param entity_event: a general event from the synchronizer
        :return: entity wrapper
        :rtype:EntityWrapper
        """
        sync_mode = entity_event['sync_mode']
        return self.transform_methods[sync_mode](entity_event)

    def _transform_snapshot_event(self, entity_event):

        entity_key = self.extract_key(entity_event)
        metadata = {
            cons.VertexProperties.NAME: entity_event[self.INSTANCE_NAME],
            cons.VertexProperties.IS_PARTIAL_DATA: False
        }

        entity_vertex = graph_utils.create_vertex(
            entity_key,
            entity_id=entity_event[self.SNAPSHOT_INSTANCE_ID],
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            entity_project=entity_event[self.PROJECT_ID],
            entity_state=entity_event[self.SNAPSHOT_INSTANCE_STATE],
            update_timestamp=entity_event[self.SNAPSHOT_TIMESTAMP],
            metadata=metadata
        )

        host_neighbor = self.create_host_neighbor(
            entity_vertex.vertex_id,
            entity_event[self.HOST_NAME])

        return base.EntityWrapper(
            entity_vertex,
            [host_neighbor],
            cons.EventAction.UPDATE)

    def _transform_init_snapshot_event(self, entity_event):

        entity_wrapper = self._transform_snapshot_event(entity_event)
        entity_wrapper.action = cons.EventAction.CREATE
        return entity_wrapper

    def _transform_update_event(self):
        pass

    # def key_fields(self):
    #     return [cons.VertexProperties.TYPE,
    #             cons.VertexProperties.SUB_TYPE,
    #             cons.VertexProperties.ID]

    def extract_key(self, entity_event):

        sync_mode = entity_event['sync_mode']

        if sync_mode == cons.SyncMode.UPDATE:
            event_id = entity_event[self.UPDATE_INSTANCE_ID]
        else:
            event_id = entity_event[self.SNAPSHOT_INSTANCE_ID]

        return self.build_instance_key(event_id)

    @staticmethod
    def build_instance_key(instance_id):

        return base.Transformer.KEY_SEPARATOR.join(
            [cons.EntityTypes.RESOURCE,
             INSTANCE_SUBTYPE,
             instance_id])

    @staticmethod
    def create_host_neighbor(vertex_id, host_name):

        host_vertex = HostTransformer.create_partial_vertex(host_name)

        relation_edge = graph_utils.create_edge(
            source_id=host_name,
            target_id=vertex_id,
            relation_type=cons.EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    @staticmethod
    def create_partial_vertex(instance_id):

        """Creates Vertex with partial data.

        Vertex with partial data contains only mandatory fields

        :param instance_id: The instance ID
        :return: Vertex with partial data
        :rtype: Vertex
        """

        metadata = {
            cons.VertexProperties.IS_PARTIAL_DATA: True
        }

        return graph_utils.create_vertex(
            InstanceTransformer.build_instance_key(instance_id),
            entity_id=instance_id,
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            metadata=metadata
        )


class HostTransformer(base.Transformer):

    def transform(self, entity_event):
        """transform

        1. transform event to Entity Vertex
        2. create neighbor list
        3. set action type

        :param entity_event:
        :return:
        """
        pass

    def extract_key(self, entity_event):
        pass

    @staticmethod
    def build_host_key(host_name):

        return base.Transformer.KEY_SEPARATOR.join(
            [cons.EntityTypes.RESOURCE,
             HOST_SUBTYPE,
             host_name])

    @staticmethod
    def create_partial_vertex(host_name):

        metadata = {
            cons.VertexProperties.IS_PARTIAL_DATA: True
        }

        return graph_utils.create_vertex(
            HostTransformer.build_host_key(host_name),
            entity_id=host_name,
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=HOST_SUBTYPE,
            metadata=metadata
        )
