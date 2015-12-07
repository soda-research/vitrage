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

import datetime

from oslo_log import log

from vitrage.common.constants import EventAction
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.processor import base as processor
from vitrage.entity_graph.processor import entity_graph_manager
from vitrage.entity_graph.transformer import base
from vitrage.entity_graph.transformer import transformer_manager
from vitrage.graph import Direction
from vitrage.graph import utils as graph_utils


LOG = log.getLogger(__name__)


class Processor(processor.ProcessorBase):

    def __init__(self):
        self.e_g_manager = entity_graph_manager.EntityGraphManager()
        self.transformer = transformer_manager.TransformerManager()
        self._initialize_events_actions()

    def process_event(self, event):
        entity = self.transform_entity(event)
        if entity.action not in self.events:
            LOG.info("error event: %s", event)
            return None

        return self.events[entity.action](entity.vertex, entity.neighbors)

    def create_entity(self, new_vertex, neighbors):
        LOG.debug("Add entity to entity graph: %s", new_vertex)

        # add the entity
        self.e_g_manager.graph.add_vertex(new_vertex)

        # add the connecting entities
        self._connect_neighbors(new_vertex, neighbors, None)

    def update_entity(self, updated_vertex, neighbors):
        LOG.debug("Update entity in entity graph: %s", updated_vertex)

        # update the entity
        curr_vertex = \
            self.e_g_manager.graph.get_vertex(updated_vertex.vertex_id)

        if not curr_vertex or self.e_g_manager.check_update_validation(
                curr_vertex, updated_vertex):
            self.e_g_manager.graph.update_vertex(updated_vertex)
            # add the connecting entities
            self._update_neighbors(updated_vertex, neighbors)
        else:
            LOG.info("Update event arrived on invalid resource: %s",
                     updated_vertex)

    def delete_entity(self, deleted_vertex, neighbors):
        LOG.debug("Delete entity from entity graph: %s", deleted_vertex)

        # update the entity
        curr_vertex = \
            self.e_g_manager.graph.get_vertex(deleted_vertex.vertex_id)

        if self.e_g_manager.check_update_validation(
                curr_vertex, deleted_vertex):
            n_vertices = self.e_g_manager.graph.neighbors(
                deleted_vertex.vertex_id, direction=Direction.BOTH)
            n_edges = self.e_g_manager.graph.get_edges(
                deleted_vertex.vertex_id, direction=Direction.BOTH)

            # delete connected edges
            for edge in n_edges:
                self.e_g_manager.mark_edge_as_deleted(edge)

            # delete partial data vertices that connected only to this vertex
            for vertex in n_vertices:
                self.e_g_manager.delete_partial_data_vertex(vertex)

            # delete vertex
            self.e_g_manager.mark_vertex_as_deleted(deleted_vertex)
        else:
            LOG.info("Delete event arrived on invalid resource: %s",
                     deleted_vertex)

    def transform_entity(self, event):
        # TODO(Alexey): change back to the original call
        # return self.transformer.transform(event)

        # create vertex
        vertex = graph_utils.create_vertex(
            'RESOURCE_INSTANCE_' + event['id'],
            entity_id=event['id'],
            entity_type='RESOURCE',
            entity_subtype='INSTANCE',
            entity_state=event[VertexProperties.STATE.lower()],
            update_timestamp=datetime.datetime.now().time(),
            is_deleted=False)

        # create neighbors
        neighbor_vertex = graph_utils.create_vertex(
            'RESOURCE_HOST_' + event['hostname'],
            entity_id=event['hostname'],
            entity_type='RESOURCE',
            entity_subtype='HOST',
            is_deleted=None)
        neighbor_edge = graph_utils.create_edge(
            neighbor_vertex.vertex_id,
            vertex.vertex_id,
            'contains',
            is_deleted=False)
        neighbors = [base.Neighbor(neighbor_vertex, neighbor_edge)]

        # decide event type
        if event['sync_mode'] == SyncMode.INIT_SNAPSHOT:
            event_type = EventAction.CREATE
        elif event['sync_mode'] == SyncMode.UPDATE:
            if event['event_type'] == 'compute.instance.volume.attach':
                event_type = EventAction.UPDATE
            elif event['event_type'] == 'compute.instance.delete.end':
                event_type = EventAction.DELETE

        return base.EntityWrapper(vertex, neighbors, event_type)

    def _update_neighbors(self, updated_vertex, neighbors):
        (valid_edges, old_edges) = self._find_edges_status(
            updated_vertex, neighbors)

        # delete old unnecessary neighbors
        self._delete_old_connections(updated_vertex, old_edges)

        # connect new neighbors
        self._connect_neighbors(updated_vertex, neighbors, valid_edges)

    def _connect_neighbors(self, updated_vertex, neighbors, valid_edges):
        for (vertex, edge) in neighbors:
            if not valid_edges or not \
                    self.e_g_manager.is_edge_exist_in_list(edge, valid_edges):
                # connect entity with neighbor
                self.e_g_manager.graph.update_vertex(vertex)
                self.e_g_manager.graph.update_edge(edge)

    def _delete_old_connections(self, updated_vertex, old_edges):
        # remove old edges and partial data vertices if exist
        for edge in old_edges:
            self.e_g_manager.mark_edge_as_deleted(edge)
            curr_ver = graph_utils.get_neighbor_vertex(
                edge, updated_vertex, self.e_g_manager.graph)
            self.e_g_manager.delete_partial_data_vertex(curr_ver)

    def _find_edges_status(self, updated_vertex, neighbors):
        valid_edges = []
        old_edges = []

        # set of all neighbor types in graph
        graph_neighbor_types = \
            self.e_g_manager.find_neighbor_types(neighbors)

        # iterate over current neighbor edges and check existence in new list
        for curr_edge in self.e_g_manager.graph.get_edges(
                updated_vertex.vertex_id, direction=Direction.BOTH):
            # check if the edge in the graph has a a connection to the
            # same type of resources in the new neighbors list
            neighbor_vertex = graph_utils.get_neighbor_vertex(
                curr_edge, updated_vertex, self.e_g_manager.graph)
            is_connection_type_exist = self.e_g_manager.get_vertex_type(
                neighbor_vertex) in graph_neighbor_types

            if not is_connection_type_exist:
                valid_edges.append(curr_edge)
                continue

            # check if the edge in the graph exists in new neighbors list
            is_equal = any(graph_utils.compare_edges(curr_edge, new_edge)
                           for (new_vertex, new_edge) in neighbors)

            if is_equal:
                valid_edges.append(curr_edge)
            else:
                old_edges.append(curr_edge)

        return (valid_edges, old_edges)

    def _initialize_events_actions(self):
        self.events = {}
        self.events[EventAction.CREATE] = self.create_entity
        self.events[EventAction.UPDATE] = self.update_entity
        self.events[EventAction.DELETE] = self.delete_entity
