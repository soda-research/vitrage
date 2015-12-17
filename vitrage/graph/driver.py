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


class Direction(object):
    OUT = 1
    IN = 2
    BOTH = 3


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
        """Set a vertex property

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
        """Delete a property from the vertex

        Example
        -------
        vertex = Vertex(vertex_id=123,
                        properties={'property_key': 'some value'})
        del(vertex['property_key'])

        :param key:
        :return:
        """
        if self.properties and key in self.properties:
            del self.properties[key]

    def __eq__(self, other):
        """Compare two vertices

        Example
        -------
        if vertex1 == vertex2:
            do something

        :type other: Vertex
        :rtype: bool
        """
        return self.__dict__ == other.__dict__ and \
            self.properties == other.properties

    def __hash__(self):
        return hash(self.vertex_id)

    def __iter__(self):
        return self.properties.itervalues()

    def __str__(self):
        return '{vertex_id : %s, properties : %s}' % \
               (str(self.vertex_id), str(self.properties))

    def get(self, k, d=None):
        return self.properties.get(k, d)


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
        """Set an edge property

        Use edge[key] instead of edge.properties[key]

        Example
        -------
        e = Edge(source_id=123, target_id=234, label='SOME_LABEL')
        e['some_key'] = 'some value'
        """
        if not self.properties:
            self.properties = {}
        self.properties[key] = value

    def __delitem__(self, key):
        """Delete a property from the edge

        Example
        -------
        edge = Edge(source_id=123, target_id=234, label='SOME_LABEL'
                    properties={'property_key': 'some value'})
        del(edge['property_key'])
        """
        if self.properties and key in self.properties:
            del self.properties[key]

    def __eq__(self, other):
        """Compare two edges

        Example
        -------
        if edge1 == edge2:
            do something

        :type other: Edge
        :rtype: bool
        """
        return self.__dict__ == other.__dict__ and \
            self.properties == other.properties

    def __hash__(self):
        return hash('%s%s%s' % (str(self.source_id), str(self.target_id),
                                str(self.label)))

    def __iter__(self):
        return self.properties.itervalues()

    def __str__(self):
        return '{source_id: %s, target_id: %s, label = %s, properties: %s}' \
               % (self.source_id, self.target_id, self.label, self.properties)

    def get(self, k, d=None):
        return self.properties.get(k, d)


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
    def num_vertex(self):
        """Number of vertices in the graph

        :return:
        :rtype: int
        """
        pass

    @abc.abstractmethod
    def num_edges(self):
        """Number of edges in the graph

        :return:
        :rtype: int
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
    def get_edges(self, v_id, direction=Direction.OUT,
                  attr_filter=None):
        """Fetch multiple edges from the graph,

        Fetch an edge from the graph, according to its two vertices and label

        EXAMPLE
        -------
        v2_edges1 = g.get_edges(
            v_id=v2.vertex_id,
            attr_filter={'LABEL': 'ON'})

        v2_edges2 = g.get_edges(
            v_id=v2.vertex_id,
            attr_filter={'LABEL': ['ON', 'WITH']})

        :param v_id: vertex id a vertex
        :type v_id: str

        :param direction: specify In/Out/Both for edge direction
        :type direction: int

        :param attr_filter: expected keys and values
        :type attr_filter: dict

        :return: All edges matching the requirements
        :rtype: list of Edge
        """
        pass

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

    @abc.abstractmethod
    def neighbors(self, v_id, vertex_attr_filter=None,
                  edge_attr_filter=None, direction=Direction.OUT):
        """Get vertices that are neighboring to v_id vertex

        To filter the neighboring vertices, specify property values for
        the vertices or for the edges connecting them.

        Example:
        --------
        graph = Graph()

        v1_prop = {'prop_key':'some value for my first vertex'}
        v2_prop = {'prop_key':'another value for my second vertex'}
        v3_prop = {'prop_key':'YES'}
        v1 = Vertex(vertex_id=1, properties=v1_prop)
        v2 = Vertex(vertex_id=2, properties=v2_prop)
        v3 = Vertex(vertex_id=3, properties=v3_prop)
        graph.add_vertex(v1)
        graph.add_vertex(v2)
        graph.add_vertex(v3)

        e_prop = {'edge_prop':'and here is my edge property value'}
        e1 = Edge(source_id=v1.vertex_id, target_id=v2.vertex_id,
                 label='BELONGS', properties=e_prop)
        e2 = Edge(source_id=v1.vertex_id, target_id=v3.vertex_id,
                 label='ON', properties=e_prop)
        graph.add_edge(e1)
        graph.add_edge(e2)

        vertices_list1 = graph.neighbors(v_id=v1.vertex_id,
                               vertex_attr_filter={'prop_key':'YES'},
                               edge_attr_filter={'LABEL':'ON})
        vertices_list2 = graph.neighbors(v_id=v1.vertex_id,
                               vertex_attr_filter={'prop_key':['YES', 'CAT']},
                               edge_attr_filter={'LABEL':['ON', 'WITH']})

        :param v_id: vertex id
        :type v_id: str
        :param vertex_attr_filter: expected keys and values
        :type vertex_attr_filter dict
        :param edge_attr_filter: expected keys and values
        :type edge_attr_filter: dict
        :return: A list of vertices that match the requested query
        :rtype: set of Vertex
        """
        pass
