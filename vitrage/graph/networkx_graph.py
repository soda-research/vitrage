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

import copy

import networkx as nx

from driver import Edge
from driver import Graph
from driver import Vertex


class NXGraph(Graph):

    GRAPH_TYPE = "networkx"

    def __init__(self, name):
        self.g = nx.MultiDiGraph()
        super(NXGraph, self).__init__(name=name, graph_type=NXGraph.GRAPH_TYPE)

    def __len__(self):
        return len(self.g)

    def copy(self):
        self_copy = NXGraph(self.name)
        self_copy.g = self.g.copy()
        return self_copy

    def add_vertex(self, v):
        """Add a vertex to the graph

        :type v: Vertex
        """
        properties_copy = copy.copy(v.properties)
        self.g.add_node(n=v.vertex_id, attr_dict=properties_copy)

    def add_edge(self, e):
        """Add an edge to the graph

        :type e: Edge
        """
        properties_copy = copy.copy(e.properties)
        self.g.add_edge(u=e.source_id, v=e.target_id,
                        key=e.label, attr_dict=properties_copy)

    def get_vertex(self, v_id):
        """Fetch a vertex from the graph

        :rtype: Vertex
        """
        properties = self.g.node.get(v_id, None)
        properties_copy = copy.copy(properties) if properties else None
        vertex = Vertex(vertex_id=v_id, properties=properties_copy)
        return vertex

    def _get_edge_properties(self, source_id, target_id, label):
        try:
            properties = self.g.adj[source_id][target_id][label]
            return properties
        except KeyError:
            return None

    def get_edge(self, source_id, target_id, label):
        """Fetch an edge from the graph,

        :rtype: Edge
        """
        properties = self._get_edge_properties(source_id, target_id, label)
        if properties:
            properties_copy = copy.copy(properties)
            item = Edge(source_id=source_id, target_id=target_id,
                        label=label, properties=properties_copy)
            return item
        else:
            return None

    def get_edges(self, source_id, target_id, labels=None, directed=True):
        """Fetch multiple edges from the graph

        :rtype: list of Edge
        """
        # TODO(ihefetz) implement this function
        pass

    def update_vertex(self, v, hard_update=False):
        """Update the vertex properties

        :type v: Vertex
        """
        if hard_update:
            properties = self.g.node.get(v.vertex_id, None)
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
        self.g.remove_node(n=v.vertex_id)

    def remove_edge(self, e):
        """Remove an edge from the graph

        :type e: Edge
        """
        self.g.remove_edge(u=e.source_id, v=e.target_id)
