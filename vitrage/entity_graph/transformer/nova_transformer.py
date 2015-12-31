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
from vitrage.common.exception import VitrageTransformerError
from vitrage.entity_graph.transformer import base
import vitrage.graph.utils as graph_utils

LOG = logging.getLogger(__name__)

INSTANCE_SUBTYPE = 'nova.instance'
HOST_SUBTYPE = 'nova.host'


class InstanceTransformer(base.Transformer):

    # Fields returned from Nova Instance snapshot
    INSTANCE_ID = {
        cons.SyncMode.SNAPSHOT: ('id',),
        cons.SyncMode.INIT_SNAPSHOT: ('id',),
        cons.SyncMode.UPDATE: ('payload', 'instance_id')
    }

    INSTANCE_STATE = {
        cons.SyncMode.SNAPSHOT: ('status',),
        cons.SyncMode.INIT_SNAPSHOT: ('status',),
        cons.SyncMode.UPDATE: ('payload', 'state')
    }

    TIMESTAMP = {
        cons.SyncMode.SNAPSHOT: ('updated',),
        cons.SyncMode.INIT_SNAPSHOT: ('updated',),
        cons.SyncMode.UPDATE: ('metadata', 'timestamp')
    }

    HOST_NAME = {
        cons.SyncMode.SNAPSHOT: ('OS-EXT-SRV-ATTR:host',),
        cons.SyncMode.INIT_SNAPSHOT: ('OS-EXT-SRV-ATTR:host',),
        cons.SyncMode.UPDATE: ('payload', 'host')
    }

    PROJECT_ID = {
        cons.SyncMode.SNAPSHOT: ('tenant_id',),
        cons.SyncMode.INIT_SNAPSHOT: ('tenant_id',),
        cons.SyncMode.UPDATE: ('payload', 'tenant_id')
    }

    INSTANCE_NAME = {
        cons.SyncMode.SNAPSHOT: ('name',),
        cons.SyncMode.INIT_SNAPSHOT: ('name',),
        cons.SyncMode.UPDATE: ('payload', 'hostname')
    }

    UPDATE_EVENT_TYPE = 'event_type'

    # Event types which need to refer them differently
    EVENT_TYPES = {
        'compute.instance.delete.end': cons.EventAction.DELETE,
        'compute.instance.create.start': cons.EventAction.CREATE
    }

    def transform(self, entity_event):
        """Transform an entity event into entity wrapper.

        Entity event is received from synchronizer it need to be
        transformed into entity wrapper. The wrapper contains:
            1. Entity Vertex - The vertex itself with all fields
            2. Neighbor list - neighbor placeholder vertex and an edge
            3. Action type - CREATE/UPDATE/DELETE

        :param entity_event: a general event from the synchronizer
        :return: entity wrapper
        :rtype:EntityWrapper
        """
        sync_mode = entity_event['sync_mode']

        field_value = base.extract_field_value

        metadata = {
            cons.VertexProperties.NAME: field_value(
                entity_event,
                self.INSTANCE_NAME[sync_mode]
            ),
            cons.VertexProperties.IS_PLACEHOLDER: False
        }

        entity_key = self.extract_key(entity_event)

        entity_id = field_value(entity_event, self.INSTANCE_ID[sync_mode])
        project = field_value(entity_event, self.PROJECT_ID[sync_mode])
        state = field_value(entity_event, self.INSTANCE_STATE[sync_mode])
        update_timestamp = field_value(
            entity_event,
            self.TIMESTAMP[sync_mode]
        )

        entity_vertex = graph_utils.create_vertex(
            entity_key,
            entity_id=entity_id,
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            entity_project=project,
            entity_state=state,
            update_timestamp=update_timestamp,
            metadata=metadata
        )

        host_neighbor = self.create_host_neighbor(
            entity_vertex.vertex_id,
            field_value(entity_event, self.HOST_NAME[sync_mode])
        )

        return base.EntityWrapper(
            entity_vertex,
            [host_neighbor],
            self._extract_action_type(entity_event))

    def _extract_action_type(self, entity_event):

        sync_mode = entity_event['sync_mode']

        if cons.SyncMode.UPDATE == sync_mode:
            return self.EVENT_TYPES.get(
                entity_event[self.UPDATE_EVENT_TYPE],
                cons.EventAction.UPDATE)

        if cons.SyncMode.SNAPSHOT == sync_mode:
            return cons.EventAction.UPDATE

        if cons.SyncMode.INIT_SNAPSHOT == sync_mode:
            return cons.EventAction.CREATE

        raise VitrageTransformerError(
            'Invalid sync mode: (%s)' % sync_mode)

    def extract_key(self, entity_event):

        instance_id = base.extract_field_value(
            entity_event,
            self.INSTANCE_ID[entity_event['sync_mode']])
        return self.build_instance_key(instance_id)

    @staticmethod
    def build_instance_key(instance_id):

        return base.Transformer.KEY_SEPARATOR.join(
            [cons.EntityTypes.RESOURCE,
             INSTANCE_SUBTYPE,
             instance_id])

    @staticmethod
    def create_host_neighbor(vertex_id, host_name):

        host_vertex = HostTransformer.create_placeholder_vertex(host_name)

        relation_edge = graph_utils.create_edge(
            source_id=host_vertex.vertex_id,
            target_id=vertex_id,
            relation_type=cons.EdgeLabels.CONTAINS
        )
        return base.Neighbor(host_vertex, relation_edge)

    @staticmethod
    def create_placeholder_vertex(instance_id):

        """Creates placeholder vertex.

        Placeholder vertex contains only mandatory fields

        :param instance_id: The instance ID
        :return: Placeholder vertex
        :rtype: Vertex
        """

        return graph_utils.create_vertex(
            InstanceTransformer.build_instance_key(instance_id),
            entity_id=instance_id,
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=INSTANCE_SUBTYPE,
            is_placeholder=True
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
    def create_placeholder_vertex(host_name):
        return graph_utils.create_vertex(
            HostTransformer.build_host_key(host_name),
            entity_id=host_name,
            entity_type=cons.EntityTypes.RESOURCE,
            entity_subtype=HOST_SUBTYPE,
            is_placeholder=True
        )
