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

"""Defines interface for Graph access and manipulation

Functions in this module are imported into the vitrage.graph namespace.
Call these functions from vitrage.graph namespace and not the
vitrage.graph.driver namespace.

"""
import abc
import six


class Vertex(object):
    """Class Vertex

    A vertex is defined as follows:
    * vertex_id is a unique identifier
    * properties is a dictionary

    """
    def __init__(self, vertex_id, properties=None):
        """Create a Vertex instance

        :type vertex_id: str
        :type properties: dict
        :rtype: Vertex
        """
        if not vertex_id:
            raise AttributeError('Attribute vertex_id is missing')
        self.vertex_id = vertex_id
        self.properties = properties

    def __getitem__(self, key):
        """Get the vertex properties

        Use vertex[key] instead of vertex.properties[key]

        Example
        -------
        v = Vertex(vertex_id=123,properties={some_key: "some_val"}
        value = v["some_key"]
        """
        return self.properties[key]

    def __setitem__(self, key, value):
        """Set the vertex properties

        Use vertex[key] instead of vertex.properties[key]

        Example
        -------
        v = Vertex(vertex_id=123,properties={some_key: "some value"}
        v["some_key"] = "another value"
        """
        if not self.properties:
            self.properties = {}
        self.properties[key] = value

    def __delitem__(self, key):
        if self.properties and key in self.properties:
            del self.properties[key]

    def __iter__(self):
        return self.properties.itervalues()


class Edge(object):
    """Class Edge represents a directional edge between two vertices

    An edge is defined as follows:
    * source_id is the first vertex id
    * target_id is the second vertex id
    * properties is a dictionary

    +---------------+    edge     +---------------+
    | source vertex |-----------> | target vertex |
    +---------------+             +---------------+

    """

    def __init__(self, source_id, target_id, label, properties=None):
        """Create an Edge instance

        :param source_id: source vertex id
        :type source_id: str

        :param target_id: target vertex id`
        :type target_id: str

        :param label:
        :type label: str

        :type properties: dict
        :rtype: Edge
        """
        if not source_id:
            raise AttributeError('Attribute source_id is missing')
        if not target_id:
            raise AttributeError('Attribute target_id is missing')
        if not label:
            raise AttributeError('Attribute label is missing')
        self.source_id = source_id
        self.target_id = target_id
        self.label = label
        self.properties = properties

    def __getitem__(self, key):
        return self.properties[key]

    def __setitem__(self, key, value):
        if not self.properties:
            self.properties = {}
        self.properties[key] = value

    def __delitem__(self, key):
        if self.properties and key in self.properties:
            del self.properties[key]

    def __iter__(self):
        return self.properties.itervalues()


@six.add_metaclass(abc.ABCMeta)
class Graph(object):
    def __init__(self, name, graph_type):
        """Create a Graph instance

        :type name: str
        :type graph_type: str
        :rtype: Graph
        """
        self.name = name
        self.graph_type = graph_type

    @abc.abstractmethod
    def copy(self):
        """Create a copy of the graph

        :return: A copy of the graph
        :rtype: Graph
        """
        pass

    @abc.abstractmethod
    def add_vertex(self, v):
        """Add a vertex to the graph

        A copy of Vertex v will be added to the graph.

        Example:
        --------
        graph = Graph()
        v = Vertex(vertex_id=1, properties={prop_key:prop_value})
        graph.add_vertex(v)

        :param v: the vertex to add
        :type v: Vertex
        """
        pass

    @abc.abstractmethod
    def add_edge(self, e):
        """Add an edge to the graph

        A copy of Edge e will be added to the graph.

        Example:
        --------
        graph = Graph()

        v1_prop = {'prop_key':'some value for my first vertex'}
        v2_prop = {'prop_key':'another value for my second vertex'}
        v1 = Vertex(vertex_id=1, properties=v1_prop)
        v2 = Vertex(vertex_id=2, properties=v2_prop)
        graph.add_vertex(v1)
        graph.add_vertex(v2)

        e_prop = {'edge_prop':'and here is my edge property value'}
        e = Edge(source_id=v1.vertex_id, target_id=v2.vertex_id,
                 label='BELONGS', properties=e_prop)
        graph.add_edge(e)

        :param e: the edge to add
        :type e: Edge
        """
        pass

    @abc.abstractmethod
    def get_vertex(self, v_id):
        """Fetch a vertex from the graph

        :param v_id: vertex id
        :type v_id: str

        :return: the vertex or None if it does not exist
        :rtype: Vertex
        """
        pass

    # TODO(ihefetz) uncomment:
    # @abc.abstractmethod
    # def get_vertices(self, properties_filter):
    #     pass

    @abc.abstractmethod
    def get_edge(self, source_id, target_id, label):
        """Fetch an edge from the graph,

        Fetch an edge from the graph, according to its two vertices and label

        :param source_id: vertex id of the source vertex
        :type source_id: str

        :param target_id: vertex id of the target vertex
        :type target_id: str

        :param label: the label property of the edge
        :type label: str

        :return: The edge between the two vertices or None
        :rtype: Edge
        """
        pass

    @abc.abstractmethod
    def get_edges(self, source_id, target_id, labels=None, directed=True):
        """Fetch multiple edges from the graph,

        Fetch an edge from the graph, according to its two vertices and label

        :param source_id: vertex id of the source vertex
        :type source_id: str

        :param target_id: vertex id of the target vertex
        :type target_id: str

        :param labels: the label property of the edge
        :type labels: str or list of str

        :param directed: consider edge direction
        :type directed: bool

        :return: The edge between the two vertices or None
        :rtype: Edge
        """
        pass

    # TODO(ihefetz) uncomment:
    # @abc.abstractmethod
    # def get_neighboring_edges(self, v_id, properties_filter):
    #     pass

    @abc.abstractmethod
    def update_vertex(self, v, hard_update=False):
        """Update the vertex properties

        Update an existing vertex and create it if non existing.
        Hard update: can be used to remove existing fields.

        :param v: the vertex with the new data
        :type v: Vertex
        :param hard_update: if True, original properties will be removed.
        :type hard_update: bool
        """
        pass

    @abc.abstractmethod
    def update_edge(self, e, hard_update=False):
        """Update the edge properties

        Update an existing edge and create it if non existing.
        Hard update: can be used to remove existing fields.

        :param e: the edge with the new data
        :type e: Edge
        :param hard_update: if True, original properties will be removed.
        :type hard_update: bool
        """
        pass

    @abc.abstractmethod
    def remove_vertex(self, v):
        """Remove Vertex v and its edges from the graph

        :type v: Vertex
        """
        pass

    @abc.abstractmethod
    def remove_edge(self, e):
        """Remove an edge from the graph

        :type e: Edge
        """
        pass

    # @abc.abstractmethod
    # def neighbors(self, v, vertex_attr=None, edge_attr=None):
    #     # TODO(ihefetz) also direction? also return the edges?
    #     """TODO(ihefetz)
    #
    #     :param v: TODO(ihefetz)
    #     :param vertex_attr: TODO(ihefetz)
    #     :param edge_attr: TODO(ihefetz)
    #     :return: TODO(ihefetz)
    #     :rtype: list of Vertex
    #     """
    #     pass
