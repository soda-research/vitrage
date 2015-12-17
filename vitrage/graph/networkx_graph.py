# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo_log import log as logging

import copy
import networkx as nx

from driver import Direction
from driver import Edge  # noqa
from driver import Graph
from driver import Vertex  # noqa
from networkx_utils import edge_copy
from networkx_utils import filter_items
from networkx_utils import vertex_copy


LOG = logging.getLogger(__name__)


class NXGraph(Graph):

    GRAPH_TYPE = "networkx"

    def __init__(self, name):
        self._g = nx.MultiDiGraph()
        super(NXGraph, self).__init__(name=name, graph_type=NXGraph.GRAPH_TYPE)

    def __len__(self):
        return len(self._g)

    def copy(self):
        self_copy = NXGraph(self.name)
        self_copy._g = self._g.copy()
        return self_copy

    def add_vertex(self, v):
        """Add a vertex to the graph

        :type v: Vertex
        """
        properties_copy = copy.copy(v.properties)
        self._g.add_node(n=v.vertex_id, attr_dict=properties_copy)

    def add_edge(self, e):
        """Add an edge to the graph

        :type e: Edge
        """
        properties_copy = copy.copy(e.properties)
        self._g.add_edge(u=e.source_id, v=e.target_id,
                         key=e.label, attr_dict=properties_copy)

    def get_vertex(self, v_id):
        """Fetch a vertex from the graph

        :rtype: Vertex
        """
        properties = self._g.node.get(v_id, None)
        if properties:
            return vertex_copy(v_id, properties)
        LOG.debug("get_vertex item not found. v_id=" + str(v_id))
        return None

    def get_edge(self, source_id, target_id, label):
        try:
            properties = self._g.adj[source_id][target_id][label]
        except KeyError:
            LOG.debug("get_edge item not found. source_id=" + str(source_id) +
                      ", target_id=" + str(target_id) +
                      ", label=" + str(label))
            return None
        if properties:
            return edge_copy(source_id, target_id, label, properties)
        return None

    def get_edges(self, v_id, direction=Direction.OUT,
                  attr_filter=None):
        """Fetch multiple edges from the graph

        :rtype: list of Edge
        """
        if not direction:
            LOG.error("get_edges: direction cannot be None")
            raise AttributeError("get_edges: direction cannot be None")

        if not v_id:
            LOG.error("get_edges: v_id cannot be None")
            raise AttributeError("get_edges: v_id cannot be None")

        edges_by_direction = self._get_edges_by_direction(v_id, direction)
        filtered_edges = filter_items(edges_by_direction, attr_filter)
        return filtered_edges

    def _get_edges_by_direction(self, v_id, direction):
        edges = set()
        if direction == Direction.BOTH:
            edges.update(self._get_edges_by_direction(v_id, Direction.IN))
            edges.update(self._get_edges_by_direction(v_id, Direction.OUT))
            return edges
        if direction == Direction.OUT:
            found_items = self._g.out_edges(nbunch=v_id, data=True, keys=True)
        else:  # IN
            found_items = self._g.in_edges(nbunch=v_id, data=True, keys=True)
        for source_id, target_id, label, data in found_items:
            edges.add(edge_copy(source_id, target_id, label, data))
        return edges

    def num_vertex(self):
        return len(self._g)

    def num_edges(self):
        return self._g.number_of_edges()

    def update_vertex(self, v, hard_update=False):
        """Update the vertex properties

        :type v: Vertex
        """
        if hard_update:
            properties = self._g.node.get(v.vertex_id, None)
            if properties:
                properties.clear()
        self.add_vertex(v)

    def update_edge(self, e, hard_update=False):
        """Update the edge properties

        :type e: Edge
        """
        if hard_update:
            properties = self._get_edge_properties(e.source_id,
                                                   e.target_id,
                                                   e.label)
            if properties:
                properties.clear()
        self.add_edge(e)

    def remove_vertex(self, v):
        """Remove Vertex v and its edges from the graph

        :type v: Vertex
        """
        self._g.remove_node(n=v.vertex_id)

    def remove_edge(self, e):
        """Remove an edge from the graph

        :type e: Edge
        """
        self._g.remove_edge(u=e.source_id, v=e.target_id, key=e.label)

    def neighbors(self, v_id, vertex_attr_filter=None, edge_attr_filter=None,
                  direction=Direction.OUT):
        if not direction:
            LOG.error("neighbors: direction cannot be None")
            raise AttributeError("neighbors: direction cannot be None")

        if not v_id:
            LOG.error("neighbors: v_id cannot be None")
            raise AttributeError("neighbors: v_id cannot be None")

        edges = self.get_edges(v_id, direction, edge_attr_filter)
        vertices_except_me = {self.get_vertex(edge.target_id)
                              if edge.source_id == v_id else
                              self.get_vertex(edge.source_id)
                              for edge in edges}
        vertices = filter_items(vertices_except_me, vertex_attr_filter)
        return vertices
