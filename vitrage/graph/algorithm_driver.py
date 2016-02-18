# Copyright 2016 - Alcatel-Lucent
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

import abc
from collections import namedtuple
import six

Mapping = namedtuple('Mapping', ['sub_graph_v_id', 'graph_v_id'])


@six.add_metaclass(abc.ABCMeta)
class GraphAlgorithm(object):

    def __init__(self, graph):
        """Create a new GraphAlgorithm

        :param graph: graph instance
        :type graph: driver.Graph
        """
        self.graph = graph

    @abc.abstractmethod
    def graph_query_vertices(self, query_dict=None, root_id=None, depth=None):
        """Create a sub graph of all the matching vertices and their edges

        BFS traversal over the graph starting from root, each vertex is
        checked according to the query. A matching vertex will be added to the
        resulting sub graph and traversal will continue to its neighbors
        :rtype: driver.Graph
        """
        pass

    @abc.abstractmethod
    def sub_graph_matching(self, sub_graph, known_mappings):
        """Search for occurrences of of a template graph in the graph

        In sub-graph matching algorithms complexity is high in the general case
        Here it is considerably mitigated  as we have an anchor in the graph.
        TODO(ihefetz)  document this

        :type known_mappings: list
        :type sub_graph: driver.Graph
        :rtype: list of dict
        """
        pass
