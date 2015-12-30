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

from dateutil import parser

from oslo_log import log

from vitrage.common.constants import EdgeProperties as EProp
from vitrage.common.constants import VertexProperties as VProp
from vitrage.common.utils import get_timezone_aware_time
from vitrage.graph import Direction
from vitrage.graph import networkx_graph

LOG = log.getLogger(__name__)


class EntityGraph(networkx_graph.NXGraph):

    def __init__(self, name):
        super(EntityGraph, self).__init__(name)

    def can_vertex_be_deleted(self, vertex):
        """Check if the vertex can be deleted

        Vertex can be deleted if it's IS_PLACEHOLDER property is
        True and if it has no neighbors that aren't marked deleted
        """

        if not vertex[VProp.IS_PLACEHOLDER]:
            return False

        # check that vertex has no neighbors
        neighbor_edges = self.get_edges(vertex.vertex_id,
                                        direction=Direction.BOTH)

        return not any(True for neighbor_edge in neighbor_edges
                       if not self.is_edge_deleted(neighbor_edge))

    def delete_placeholder_vertex(self, suspected_vertex):
        """Checks if it is a placeholder vertex, and if so deletes it """

        if self.can_vertex_be_deleted(suspected_vertex):
            LOG.debug("Delete placeholder vertex: %s", suspected_vertex)
            self.remove_vertex(suspected_vertex)

    def is_vertex_deleted(self, vertex):
        return vertex.get(VProp.IS_DELETED, False)

    def is_edge_deleted(self, edge):
        return edge.get(EProp.IS_DELETED, False)

    def mark_vertex_as_deleted(self, vertex):
        """Marks the vertex as is deleted, and updates deletion timestamp"""

        vertex[VProp.IS_DELETED] = True
        vertex[VProp.VERTEX_DELETION_TIMESTAMP] = get_timezone_aware_time()
        self.update_vertex(vertex)

    def mark_edge_as_deleted(self, edge):
        """Marks the edge as is deleted, and updates delete timestamp"""

        edge[EProp.IS_DELETED] = True
        edge[EProp.EDGE_DELETION_TIMESTAMP] = get_timezone_aware_time()
        self.update_edge(edge)

    def find_neighbor_types(self, neighbors):
        """Finds all the types (TYPE, SUB_TYPE) of the neighbors """

        neighbor_types = set()
        for (vertex, edge) in neighbors:
            neighbor_types.add(self.get_vertex_type(vertex))
        return neighbor_types

    def get_vertex_type(self, vertex):
        type = vertex[VProp.TYPE]
        sub_type = vertex[VProp.SUB_TYPE]
        return (type, sub_type)

    def check_update_validation(self, graph_vertex, updated_vertex):
        """Checks current and updated validation

        Check 2 conditions:
        1. is the vertex not deleted
        2. is updated timestamp bigger then current timestamp
        """

        return (not self.is_vertex_deleted(graph_vertex)) and \
            self.check_timestamp(graph_vertex, updated_vertex)

    def check_timestamp(self, graph_vertex, new_vertex):
        curr_timestamp = graph_vertex.get(VProp.UPDATE_TIMESTAMP)
        if not curr_timestamp:
            return True

        current_time = parser.parse(curr_timestamp)
        new_time = parser.parse(new_vertex[VProp.UPDATE_TIMESTAMP])
        return current_time <= new_time

    def can_update_vertex(self, graph_vertex, new_vertex):
        return (not graph_vertex) or \
            (not (not graph_vertex[VProp.IS_PLACEHOLDER]
                  and new_vertex[VProp.IS_PLACEHOLDER]))
