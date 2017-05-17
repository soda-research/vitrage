# Copyright 2015 - Alcatel-Lucent
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

from oslo_log import log

from oslo_utils import uuidutils

from vitrage.common.constants import GraphAction
from vitrage.common.constants import VertexProperties as VProps
from vitrage.common.exception import VitrageError
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.transformer_base import TransformerBase
from vitrage.entity_graph.mappings.datasource_info_mapper import \
    DatasourceInfoMapper
from vitrage.entity_graph.processor import base as processor
from vitrage.entity_graph.processor.notifier import GraphNotifier
from vitrage.entity_graph.processor import processor_utils as PUtils
from vitrage.entity_graph.transformer_manager import TransformerManager
from vitrage.graph import Direction
from vitrage.graph.driver.networkx_graph import NXGraph

LOG = log.getLogger(__name__)


class Processor(processor.ProcessorBase):

    def __init__(self, conf, initialization_status, e_graph=None,
                 uuid=False):
        super(Processor, self).__init__()
        self.conf = conf
        self.transformer_manager = TransformerManager(self.conf)
        self.state_manager = DatasourceInfoMapper(self.conf)
        self._initialize_events_actions()
        self.initialization_status = initialization_status
        self.entity_graph = e_graph if e_graph is not None\
            else NXGraph("Entity Graph", uuid=uuid)
        self._notifier = GraphNotifier(conf)

    def process_event(self, event):
        """Decides which action to run on given event

        Transforms the event into a tuple (vertex, neighbors,action).
        After transforming, it runs the correct action according to the
        action received from the transformer.

        :param event: The event to be processed
        :type event: Dictionary
        """

        LOG.debug('processor event:\n%s', event)

        self._enrich_event(event)
        entity = self.transformer_manager.transform(event)
        self._calculate_aggregated_state(entity.vertex, entity.action)
        self.actions[entity.action](entity.vertex, entity.neighbors)

    def create_entity(self, new_vertex, neighbors):
        """Adds new vertex to the entity graph

        Adds the entity to the entity graph, and connects it's neighbors

        :param new_vertex: The new vertex to add to graph
        :type new_vertex: Vertex

        :param neighbors: The neighbors of the new vertex
        :type neighbors: List
        """

        LOG.debug('Add entity to entity graph:\n%s', new_vertex)
        # TODO(doffek): check if it's possible to move the
        # _find_and_fix_graph_vertex method call to the process_event method
        # so it will be done in one central place
        self._find_and_fix_graph_vertex(new_vertex, neighbors)
        self.entity_graph.add_vertex(new_vertex)
        self._connect_neighbors(neighbors, set(), GraphAction.CREATE_ENTITY)

    def update_entity(self, updated_vertex, neighbors):
        """Updates the vertex in the entity graph

        Updates the in entity in the entity graph. In addition it removes old
        neighbor connections, and connects the new neighbors.

        :param updated_vertex: The vertex to be updated in the graph
        :type updated_vertex: Vertex

        :param neighbors: The neighbors of the updated vertex
        :type neighbors: List
        """

        LOG.debug('Update entity in entity graph:\n%s', updated_vertex)

        if not updated_vertex.get(VProps.IS_REAL_VITRAGE_ID, False):
            self._find_and_fix_graph_vertex(updated_vertex, neighbors)
        graph_vertex = self.entity_graph.get_vertex(updated_vertex.vertex_id)

        if (not graph_vertex) or \
                PUtils.is_newer_vertex(graph_vertex, updated_vertex):
            PUtils.update_entity_graph_vertex(self.entity_graph,
                                              graph_vertex,
                                              updated_vertex)
            self._update_neighbors(updated_vertex, neighbors)
        else:
            LOG.warning("Update event arrived on invalid resource: %s",
                        updated_vertex)

    def delete_entity(self, deleted_vertex, neighbors):
        """Deletes the vertex from the entity graph

        Marks the corresponding vertex and its edges as deleted

        :param deleted_vertex: The vertex to be deleted from the graph
        :type deleted_vertex: Vertex

        :param neighbors: The neighbors of the deleted vertex
        :type neighbors: List
        """

        LOG.debug('Delete entity from entity graph:\n%s', deleted_vertex)
        if not deleted_vertex.get(VProps.IS_REAL_VITRAGE_ID, False):
            self._find_and_fix_graph_vertex(deleted_vertex, neighbors)
        graph_vertex = self.entity_graph.get_vertex(deleted_vertex.vertex_id)

        if graph_vertex and (not PUtils.is_deleted(graph_vertex)) and \
                PUtils.is_newer_vertex(graph_vertex, deleted_vertex):
            neighbor_vertices = self.entity_graph.neighbors(
                deleted_vertex.vertex_id)
            neighbor_edges = self.entity_graph.get_edges(
                deleted_vertex.vertex_id)

            for edge in neighbor_edges:
                PUtils.mark_deleted(self.entity_graph, edge)

            for vertex in neighbor_vertices:
                PUtils.delete_placeholder_vertex(self.entity_graph, vertex)

            PUtils.mark_deleted(self.entity_graph, deleted_vertex)
        else:
            LOG.warning("Delete event arrived on invalid resource: %s",
                        deleted_vertex)

    def update_relationship(self, entity_vertex, neighbors):
        LOG.debug('Update relationship in entity graph:\n%s', neighbors)

        if not entity_vertex:
            for neighbor in neighbors:
                self.entity_graph.update_edge(neighbor.edge)
            return

        # TODO(doffek): check if we need here the update_vertex because the
        # purpose of this method is to update the relationship
        self._find_and_fix_graph_vertex(entity_vertex, [])
        self.entity_graph.update_vertex(entity_vertex)
        for neighbor in neighbors:
            self._find_and_fix_relationship(entity_vertex, neighbor)
            self.entity_graph.update_edge(neighbor.edge)

    def delete_relationship(self, updated_vertex, neighbors):
        LOG.debug('Delete relationship from entity graph:\n%s', neighbors)

        if not updated_vertex:
            for neighbor in neighbors:
                graph_edge = self.entity_graph.get_edge(
                    neighbor.edge.source_id,
                    neighbor.edge.target_id,
                    neighbor.edge.label)
            if graph_edge:
                self.entity_graph.remove_edge(graph_edge)

            return

        # TODO(doffek): check if we need here the update_vertex because the
        # purpose of this method is to update the relationship
        self._find_and_fix_graph_vertex(updated_vertex, [])
        self.entity_graph.update_vertex(updated_vertex)
        for neighbor in neighbors:
            self._find_and_fix_relationship(updated_vertex, neighbor)
            graph_edge = self.entity_graph.get_edge(neighbor.edge.source_id,
                                                    neighbor.edge.target_id,
                                                    neighbor.edge.label)
            if graph_edge:
                PUtils.mark_deleted(self.entity_graph, graph_edge)

    def remove_deleted_entity(self, vertex, neighbors):
        """Removes the deleted vertex from the entity graph

        Removes vertex that it's is_deleted value is True

        :param vertex: The vertex to be removed from the graph
        :type vertex: Vertex

        :param neighbors: The neighbors of the deleted vertex
        :type neighbors: List - It's just a mock in this method
        """

        LOG.debug('Remove deleted entity from entity graph:\n%s', vertex)

        graph_vertex = self.entity_graph.get_vertex(vertex.vertex_id)

        if graph_vertex and PUtils.is_deleted(graph_vertex) and \
                PUtils.is_newer_vertex(graph_vertex, vertex):
            self.entity_graph.remove_vertex(vertex)
        else:
            LOG.warning("Delete event arrived on invalid resource: %s", vertex)

    def handle_end_message(self, vertex, neighbors):
        self.initialization_status.end_messages[vertex[VProps.TYPE]] = True

        if len(self.initialization_status.end_messages) == \
                len(self.conf.datasources.types):
            self.initialization_status.status = \
                self.initialization_status.RECEIVED_ALL_END_MESSAGES
            self.do_on_initialization_end()

    def do_on_initialization_end(self):
        if self._notifier.enabled:
            self.entity_graph.subscribe(self._notifier.notify_when_applicable)
            LOG.info('Graph notifications subscription added')

    def _update_neighbors(self, vertex, neighbors):
        """Updates vertices neighbor connections

        1. Removes old neighbor connections
        2. connects the new neighbors.
        """

        (valid_edges, obsolete_edges) = self._find_edges_status(vertex,
                                                                neighbors)
        self._delete_old_connections(vertex, obsolete_edges)
        self._connect_neighbors(neighbors,
                                valid_edges,
                                GraphAction.UPDATE_ENTITY)

    def _connect_neighbors(self, neighbors, valid_edges, action):
        """Updates the neighbor vertex and adds the connection edges """
        if not neighbors:
            LOG.debug('connect_neighbors - nothing to do')
            return

        LOG.debug("Connect neighbors. Neighbors: %s, valid_edges: %s",
                  neighbors, valid_edges)
        for (vertex, edge) in neighbors:
            graph_vertex = self.entity_graph.get_vertex(vertex.vertex_id)
            if not graph_vertex or not PUtils.is_deleted(graph_vertex):
                if PUtils.can_update_vertex(graph_vertex, vertex):
                    LOG.debug("Updates vertex: %s", vertex)
                    self._calculate_aggregated_state(vertex, action)
                    PUtils.update_entity_graph_vertex(self.entity_graph,
                                                      graph_vertex,
                                                      vertex)

                if edge not in valid_edges:
                    LOG.debug("Updates edge: %s", edge)
                    self.entity_graph.update_edge(edge)
            else:
                LOG.debug("neighbor vertex wasn't updated: %s", vertex)

    def _delete_old_connections(self, vertex, obsolete_edges):
        """Deletes the "vertex" old connections

        Finds the old connections that are connected to updated_vertex,
        and marks them as deleted
        """
        if not obsolete_edges:
            LOG.debug('obsolete_edges - nothing to do')
            return

        LOG.debug('Delete old connections. Vertex:\n%s', vertex)
        # remove old edges and placeholder vertices if exist
        for edge in obsolete_edges:
            LOG.debug("Delete obsolete edge:\n%s", edge)
            PUtils.mark_deleted(self.entity_graph, edge)
            graph_ver = self.entity_graph.get_vertex(
                edge.other_vertex(vertex.vertex_id))
            PUtils.delete_placeholder_vertex(self.entity_graph, graph_ver)

    def _find_edges_status(self, vertex, neighbors):
        """Finds "vertex" valid and old connections

        Checks all the edges that are connected to the vertex in the entity
        graph, and finds which of them are old connections (edges that are no
        longer connected to those entities), and which are valid connections.
        """

        valid_edges = set()
        obsolete_edges = set()

        graph_neighbor_types = \
            PUtils.find_neighbor_types(neighbors)

        neighbor_edges = set(e for v, e in neighbors)
        for curr_edge in self.entity_graph.get_edges(vertex.vertex_id,
                                                     direction=Direction.BOTH):
            # check if the edge in the graph has a a connection to the
            # same type of resources in the new neighbors list
            neighbor_vertex = self.entity_graph.get_vertex(
                curr_edge.other_vertex(vertex.vertex_id))

            is_connection_type_exist = PUtils.get_vertex_types(
                neighbor_vertex) in graph_neighbor_types

            if not is_connection_type_exist:
                valid_edges.add(curr_edge)
                continue

            if curr_edge in neighbor_edges:
                valid_edges.add(curr_edge)
            else:
                obsolete_edges.add(curr_edge)

        return valid_edges, obsolete_edges

    def _initialize_events_actions(self):
        self.actions = {
            GraphAction.CREATE_ENTITY: self.create_entity,
            GraphAction.UPDATE_ENTITY: self.update_entity,
            GraphAction.DELETE_ENTITY: self.delete_entity,
            GraphAction.UPDATE_RELATIONSHIP: self.update_relationship,
            GraphAction.DELETE_RELATIONSHIP: self.delete_relationship,
            GraphAction.REMOVE_DELETED_ENTITY: self.remove_deleted_entity,
            # should not be called explicitly
            GraphAction.END_MESSAGE: self.handle_end_message
        }

    def _calculate_aggregated_state(self, vertex, action):
        LOG.debug("calculate event state")

        try:
            if action in [GraphAction.UPDATE_ENTITY,
                          GraphAction.DELETE_ENTITY,
                          GraphAction.CREATE_ENTITY]:
                if vertex.get(VProps.IS_REAL_VITRAGE_ID, False):
                    graph_vertex = self.entity_graph.get_vertex(
                        vertex.vertex_id)
                else:
                    graph_vertex = self._get_single_graph_vertex_by_props(
                        vertex)
            elif action in [GraphAction.END_MESSAGE,
                            GraphAction.REMOVE_DELETED_ENTITY,
                            GraphAction.UPDATE_RELATIONSHIP,
                            GraphAction.DELETE_RELATIONSHIP]:
                return None
            else:
                LOG.error('unrecognized action: %s for vertex: %s',
                          action, vertex)
                return None

            self.state_manager.aggregated_state(vertex, graph_vertex)
        except Exception as e:
            LOG.exception("Calculate aggregated state failed - %s", e)

    def _enrich_event(self, event):
        attr = self.transformer_manager.get_enrich_query(event)
        if attr is None:
            return
        result = self.entity_graph.get_vertices(attr)
        event[TransformerBase.QUERY_RESULT] = result

    def _find_and_fix_relationship(self, vertex, neighbor):
        prev_neighbor_id = neighbor.vertex[VProps.VITRAGE_ID]
        self._find_and_fix_graph_vertex(neighbor.vertex, [])
        if neighbor.edge.source_id == prev_neighbor_id:
            neighbor.edge.source_id = neighbor.vertex.vertex_id
            neighbor.edge.target_id = vertex.vertex_id
        else:
            neighbor.edge.target_id = neighbor.vertex.vertex_id
            neighbor.edge.source_id = vertex.vertex_id

    def _find_and_fix_graph_vertex(self,
                                   vertex,
                                   neighbors=None,
                                   include_deleted=False):
        """Search for vertex in graph, and update vertex id and vitrage ID

        Search for vertex in graph, and update vertex id and vitrage ID
        Both in the Vertex itself, and in it's neighbors and edges

        :param new_vertex: The vertex to update
        :type new_vertex: Vertex

        :param neighbors: The neighbors of the vertex
        :type neighbors: list

        :param include_deleted: If True, Include deleted entities in the search
        :type include_deleted: bool
        """

        previous_vitrage_id = vertex[VProps.VITRAGE_ID]

        graph_vertex = self._get_single_graph_vertex_by_props(
            vertex, include_deleted)

        if not graph_vertex or (PUtils.is_deleted(graph_vertex)
                                and not include_deleted):

            vitrage_id = uuidutils.generate_uuid()
            if vertex[VProps.TYPE] == OPENSTACK_CLUSTER:
                self.entity_graph.root_id = vitrage_id
        else:
            vitrage_id = graph_vertex[VProps.VITRAGE_ID]

        vertex[VProps.VITRAGE_ID] = vitrage_id
        vertex.vertex_id = vitrage_id

        if not neighbors:
            return

        for neighbor_vertex, edge in neighbors:
            if not neighbor_vertex.get(VProps.IS_REAL_VITRAGE_ID, False):
                self._find_and_fix_graph_vertex(neighbor_vertex)
            if edge.target_id == previous_vitrage_id:
                edge.target_id = vitrage_id
                edge.source_id = neighbor_vertex.vertex_id
            else:
                edge.source_id = vitrage_id
                edge.target_id = neighbor_vertex.vertex_id

    def _get_single_graph_vertex_by_props(self, vertex, include_deleted=False):
        """Returns a single vertex by it's defining properties

        Queries the graph DB for vertices according to the
        vertice's "key" properties
        In case multiple vertices return from the query,
        an exception is issued

        :param updated_vertex: The vertex with the defining properties
        :type vertex: Vertex

        :param include_deleted: Include deleted entities in the query
        :type include_deleted: bool
        """

        received_graph_vertices = self.entity_graph.get_vertices_by_key(
            PUtils.get_defining_properties(vertex))
        graph_vertices = []
        if include_deleted:
            for tmp_vertex in received_graph_vertices:
                graph_vertices.append(tmp_vertex)
        else:
            for tmp_vertex in received_graph_vertices:
                if not tmp_vertex.get(VProps.IS_DELETED, False):
                    graph_vertices.append(tmp_vertex)

        if len(graph_vertices) > 1:
            raise VitrageError(
                'found too many vertices with same properties: %s ',
                vertex)
        graph_vertex = None if not graph_vertices else graph_vertices[0]

        return graph_vertex
