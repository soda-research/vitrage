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

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import NXGraph
from vitrage.utils.datetime import utcnow


LOG = log.getLogger(__name__)


class EntityGraph(NXGraph):

    def __init__(self, name, root_id=None):
        super(EntityGraph, self).__init__(name, root_id)

    def can_vertex_be_deleted(self, vertex):
        """Check if the vertex can be deleted

        Vertex can be deleted if it's IS_PLACEHOLDER property is
        True and if it has no neighbors that aren't marked deleted
        """

        if not vertex[VProps.IS_PLACEHOLDER]:
            return False

        # check that vertex has no neighbors
        neighbor_edges = self.get_edges(vertex.vertex_id)

        return not any(True for neighbor_edge in neighbor_edges
                       if not self.is_edge_deleted(neighbor_edge))

    def delete_placeholder_vertex(self, suspected_vertex):
        """Checks if it is a placeholder vertex, and if so deletes it """

        if self.can_vertex_be_deleted(suspected_vertex):
            LOG.debug("Delete placeholder vertex: %s", suspected_vertex)
            self.remove_vertex(suspected_vertex)

    @staticmethod
    def is_vertex_deleted(vertex):
        return vertex.get(VProps.IS_DELETED, False)

    @staticmethod
    def is_edge_deleted(edge):
        return edge.get(EProps.IS_DELETED, False)

    def mark_vertex_as_deleted(self, vertex):
        """Marks the vertex as is deleted, and updates deletion timestamp"""
        vertex[VProps.IS_DELETED] = True
        vertex[VProps.SAMPLE_TIMESTAMP] = str(utcnow())
        self.update_vertex(vertex)

    def mark_edge_as_deleted(self, edge):
        """Marks the edge as is deleted, and updates delete timestamp"""
        edge[EProps.IS_DELETED] = True
        edge[EProps.UPDATE_TIMESTAMP] = str(utcnow())
        self.update_edge(edge)

    def find_neighbor_types(self, neighbors):
        """Finds all the types (TYPE, SUB_TYPE) of the neighbors """

        neighbor_types = set()
        for (vertex, edge) in neighbors:
            neighbor_types.add(self.get_vertex_category(vertex))
        return neighbor_types

    @staticmethod
    def get_vertex_category(vertex):
        category = vertex[VProps.CATEGORY]
        type_ = vertex[VProps.TYPE]
        return category, type_

    @staticmethod
    def can_update_vertex(graph_vertex, new_vertex):
        return (not graph_vertex) or (not new_vertex[VProps.IS_PLACEHOLDER])

    def update_entity_graph_vertex(self, graph_vertex, updated_vertex):
        if updated_vertex[VProps.IS_PLACEHOLDER] and \
                graph_vertex and not graph_vertex[VProps.IS_PLACEHOLDER]:

            updated_vertex[VProps.IS_PLACEHOLDER] = False
            updated_vertex[VProps.IS_DELETED] = graph_vertex[VProps.IS_DELETED]

        self.update_vertex(updated_vertex)
