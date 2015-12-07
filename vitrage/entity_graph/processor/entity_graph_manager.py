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

from vitrage.common.constants import EdgeProperties
from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.transformer import transformer_manager
from vitrage.graph import create_graph
from vitrage.graph import Direction
from vitrage.graph import utils

LOG = log.getLogger(__name__)


class EntityGraphManager(object):

    def __init__(self):
        super(EntityGraphManager, self).__init__()
        self.graph = create_graph('entity graph')
        self.transformer = transformer_manager.TransformerManager()

    def is_partial_data_vertex(self, vertex):
        # check that vertex has no neighbors
        neighbor_edges = self.graph.get_edges(vertex.vertex_id,
                                              direction=Direction.BOTH)
        for neighbor_edge in neighbor_edges:
            if not self.is_edge_deleted(neighbor_edge):
                return False

        # check properties
        # TODO(Alexey): implement get_vertex_essential_properties
        # key_properties = self.transformer.key_fields(vertex)
        key_properties = [VertexProperties.TYPE, VertexProperties.SUB_TYPE,
                          VertexProperties.ID]

        return not any(True for prop in vertex.properties
                       if prop not in key_properties)

    def delete_partial_data_vertex(self, suspected_vertex):
        if self.is_partial_data_vertex(suspected_vertex):
            LOG.debug("Delete partial data vertex: %s", suspected_vertex)
            self.graph.remove_vertex(suspected_vertex)

    def is_vertex_deleted(self, vertex):
        return vertex.properties.get(
            VertexProperties.IS_VERTEX_DELETED, False)

    def is_edge_deleted(self, edge):
        return edge.properties.get(
            EdgeProperties.IS_EDGE_DELETED, False)

    def mark_vertex_as_deleted(self, vertex):
        vertex.properties[VertexProperties.IS_VERTEX_DELETED] = True
        vertex.properties[VertexProperties.VERTEX_DELETION_TIMESTAMP] = \
            datetime.datetime.now()
        self.graph.update_vertex(vertex)

    def mark_edge_as_deleted(self, edge):
        edge.properties[EdgeProperties.IS_EDGE_DELETED] = True
        edge.properties[EdgeProperties.EDGE_DELETION_TIMESTAMP] = \
            datetime.datetime.now()
        self.graph.update_edge(edge)

    def find_neighbor_types(self, neighbors):
        neighbor_types = set()
        for (vertex, edge) in neighbors:
            neighbor_types.add(self.get_vertex_type(vertex))
        return neighbor_types

    def get_vertex_type(self, vertex):
        type = vertex.properties[VertexProperties.TYPE]
        sub_type = vertex.properties[VertexProperties.SUB_TYPE]
        return (type, sub_type)

    def check_update_validation(self, curr_vertex, updated_vertex):
        return not self.is_vertex_deleted(curr_vertex) and \
            self.check_timestamp(curr_vertex, updated_vertex)

    def is_edge_exist_in_list(self, edge, edges_list):
        return any(utils.compare_edges(edge_in_list, edge)
                   for edge_in_list in edges_list)

    def check_timestamp(self, curr_vertex, new_vertex):
        is_timestamp_property_exist = VertexProperties.UPDATE_TIMESTAMP \
            not in curr_vertex.properties.keys()
        is_old = curr_vertex.properties[VertexProperties.UPDATE_TIMESTAMP] <= \
            new_vertex.properties[VertexProperties.UPDATE_TIMESTAMP]
        return is_timestamp_property_exist or is_old
