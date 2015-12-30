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

from oslo_log import log

from vitrage.common.constants import EventAction
from vitrage.entity_graph.processor import base as processor
from vitrage.entity_graph.processor import entity_graph_manager
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
        """Decides which action to run on given event

        Transforms the event into a tupple (vertex, neighbors,action).
        After transforming, it runs the correct action according to the
        action received from the transformer.

        :param event: The event to be processed
        :type event: Dictionary
        """

        entity = self.transform_entity(event)
        if entity.action not in self.actions:
            LOG.info("error event: %s", event)
            return None

        return self.actions[entity.action](entity.vertex, entity.neighbors)

    def create_entity(self, new_vertex, neighbors):
        """Adds new vertex to the entity graph

        Adds the entity to the entity graph, and connects it's neighbors

        :param new_vertex: The new vertex to add to graph
        :type new_vertex: Vertex

        :param neighbors: The neighbors of the new vertex
        :type neighbors: List
        """

        LOG.debug("Add entity to entity graph: %s", new_vertex)
        self.e_g_manager.graph.add_vertex(new_vertex)
        self._connect_neighbors(neighbors, None)

    def update_entity(self, updated_vertex, neighbors):
        """Updates the vertex in the entity graph

        Updates the in entity in the entity graph. In addition it removes old
        neighbor connections, and connects the new neighbors.

        :param updated_vertex: The vertex to be updated in the graph
        :type updated_vertex: Vertex

        :param neighbors: The neighbors of the updated vertex
        :type neighbors: List
        """

        LOG.debug("Update entity in entity graph: %s", updated_vertex)

        curr_vertex = \
            self.e_g_manager.graph.get_vertex(updated_vertex.vertex_id)

        if (not curr_vertex) or self.e_g_manager.check_update_validation(
                curr_vertex, updated_vertex):
            self.e_g_manager.graph.update_vertex(updated_vertex)
            # add the connecting entities
            self._update_neighbors(updated_vertex, neighbors)
        else:
            LOG.info("Update event arrived on invalid resource: %s",
                     updated_vertex)

    def delete_entity(self, deleted_vertex, neighbors):
        """Deletes the vertex from the entity graph

        Marks the corresponding vertex and its edges as deleted

        :param deleted_vertex: The vertex to be deleted from the graph
        :type deleted_vertex: Vertex

        :param neighbors: The neighbors of the deleted vertex
        :type neighbors: List
        """

        LOG.debug("Delete entity from entity graph: %s", deleted_vertex)

        curr_vertex = \
            self.e_g_manager.graph.get_vertex(deleted_vertex.vertex_id)

        if (not curr_vertex) or self.e_g_manager.check_update_validation(
                curr_vertex, deleted_vertex):
            neighbor_vertices = self.e_g_manager.graph.neighbors(
                deleted_vertex.vertex_id, direction=Direction.BOTH)
            neighbor_edges = self.e_g_manager.graph.get_edges(
                deleted_vertex.vertex_id, direction=Direction.BOTH)

            # delete connected edges
            for edge in neighbor_edges:
                self.e_g_manager.mark_edge_as_deleted(edge)

            # delete placeholder vertices that connected only to this vertex
            for vertex in neighbor_vertices:
                self.e_g_manager.delete_placeholder_vertex(vertex)

            # delete vertex
            self.e_g_manager.mark_vertex_as_deleted(deleted_vertex)
        else:
            LOG.info("Delete event arrived on invalid resource: %s",
                     deleted_vertex)

    def transform_entity(self, event):
        return self.transformer.transform(event)

    def _update_neighbors(self, vertex, neighbors):
        """Updates vertices neighbor connections

        1. Removes old neighbor connections
        2. connects the new neighbors.
        """

        (valid_edges, old_edges) = self._find_edges_status(
            vertex, neighbors)
        self._delete_old_connections(vertex, old_edges)
        self._connect_neighbors(neighbors, valid_edges)

    def _connect_neighbors(self, neighbors, valid_edges):
        """Updates the neighbor vertex and adds the connection edges """

        LOG.debug("Connect neighbors. Neighbors: %s, valid_edges: %s",
                  neighbors, valid_edges)
        for (vertex, edge) in neighbors:
            curr_vertex = self.e_g_manager.graph.get_vertex(vertex.vertex_id)
            if (not curr_vertex) or self.e_g_manager.check_update_validation(
                    curr_vertex, vertex):
                if self.e_g_manager.can_update_vertex(curr_vertex, vertex):
                    self.e_g_manager.graph.update_vertex(vertex)

                if not valid_edges or not \
                    self.e_g_manager.is_edge_exist_in_list(edge, valid_edges):
                    self.e_g_manager.graph.update_edge(edge)

    def _delete_old_connections(self, vertex, old_edges):
        """Deletes the "vertex" old connections

        Finds the old connections that are connected to updated_vertex,
        and marks them as deleted
        """

        LOG.debug("Delete old connections. Vertex: %s, old edges: %s",
                  vertex, old_edges)
        # remove old edges and placeholder vertices if exist
        for edge in old_edges:
            self.e_g_manager.mark_edge_as_deleted(edge)
            curr_ver = graph_utils.get_neighbor_vertex(
                edge, vertex, self.e_g_manager.graph)
            self.e_g_manager.delete_placeholder_vertex(curr_ver)

    def _find_edges_status(self, vertex, neighbors):
        """Finds "vertex" valid and old connections

        Checks all the edges that are connected to the vertex in the entity
        graph, and finds which of them are old connections (edges that are no
        longer connected to those entities), and which are valid connections.
        """

        valid_edges = []
        old_edges = []

        # set of all neighbor types in graph
        graph_neighbor_types = \
            self.e_g_manager.find_neighbor_types(neighbors)

        # iterate over current neighbor edges and check existence in new list
        for curr_edge in self.e_g_manager.graph.get_edges(
                vertex.vertex_id, direction=Direction.BOTH):
            # check if the edge in the graph has a a connection to the
            # same type of resources in the new neighbors list
            neighbor_vertex = graph_utils.get_neighbor_vertex(
                curr_edge, vertex, self.e_g_manager.graph)
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
        self.actions = {}
        self.actions[EventAction.CREATE] = self.create_entity
        self.actions[EventAction.UPDATE] = self.update_entity
        self.actions[EventAction.DELETE] = self.delete_entity
