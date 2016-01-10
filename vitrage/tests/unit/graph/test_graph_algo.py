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

"""
test_vitrage graph algorithms
----------------------------------

Tests for `vitrage` graph driver algorithms
"""
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import create_algorithm
from vitrage.tests.unit.graph.base import *  # noqa


class GraphAlgorithmTest(GraphTestBase):

    def test_graph_query_vertices(self):
        ga = create_algorithm(self.entity_graph)

        query = {'==': {VProps.SUB_TYPE: NODE}}
        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            1,  # For NODE
            subgraph.num_vertex(), 'num of vertex node')

        query = {
            'or': [
                {'==': {VProps.SUB_TYPE: HOST}},
                {'==': {VProps.SUB_TYPE: NODE}}
            ]
        }

        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            ENTITY_GRAPH_HOSTS_PER_NODE,
            subgraph.num_edges(), 'num of edges Host <-- NODE')

        query = {
            'or': [
                {'==': {VProps.SUB_TYPE: INSTANCE}},
                {'==': {VProps.TYPE: ALARM}},
                {'==': {VProps.SUB_TYPE: HOST}},
                {'==': {VProps.SUB_TYPE: NODE}}
            ]
        }
        subgraph = ga.graph_query_vertices(query)
        self.assertEqual(
            ENTITY_GRAPH_HOSTS_PER_NODE +
            ENTITY_GRAPH_HOSTS_PER_NODE * ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_NODE * ENTITY_GRAPH_VMS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_NODE * ENTITY_GRAPH_VMS_PER_HOST *
            ENTITY_GRAPH_ALARMS_PER_VM,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        # Get first host ID
        neighboring_hosts = self.entity_graph.neighbors(
            v_node.vertex_id, {VProps.SUB_TYPE: HOST})
        first_host_id = neighboring_hosts.pop().vertex_id

        query = {'!=': {'NOTHING': 'IS EVERYTHING'}}
        subgraph = ga.graph_query_vertices(
            query_dict=query, root_id=first_host_id, depth=1)
        self.assertEqual(
            1 +  # For tye host
            1 +  # For NODE
            1 +  # For SWITCH
            ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        query = {
            'or': [
                {'==': {VProps.SUB_TYPE: SWITCH}},
                {'==': {VProps.SUB_TYPE: HOST}},
            ]
        }
        subgraph = ga.graph_query_vertices(
            query_dict=query, root_id=first_host_id, depth=1)
        self.assertEqual(
            1,  # For SWITCH
            subgraph.num_edges(), 'num of BOTH edges Host (depth 1)')

        subgraph = ga.graph_query_vertices(root_id=first_host_id, depth=2)
        self.assertEqual(
            1 +  # Node to switch
            ENTITY_GRAPH_HOSTS_PER_NODE * 2 +
            ENTITY_GRAPH_ALARMS_PER_HOST +
            ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST +
            ENTITY_GRAPH_VMS_PER_HOST * ENTITY_GRAPH_ALARMS_PER_VM,
            subgraph.num_edges(), 'num of BOTH edges Host (depth 2)')

        query = {
            'and': [
                {'!=': {VProps.SUB_TYPE: ALARM_ON_VM}},
                {'!=': {VProps.SUB_TYPE: ALARM_ON_HOST}},
                {'!=': {VProps.TYPE: ALARM}}
            ]
        }
        subgraph = ga.graph_query_vertices(query_dict=query, depth=3)
        self.assertEqual(
            1 +  # Node to switch
            ENTITY_GRAPH_HOSTS_PER_NODE * 2 +
            ENTITY_GRAPH_HOSTS_PER_NODE * ENTITY_GRAPH_TESTS_PER_HOST +
            ENTITY_GRAPH_HOSTS_PER_NODE * ENTITY_GRAPH_VMS_PER_HOST,
            subgraph.num_edges(), 'num of edges Node (depth 3)')

        query = {
            'or': [
                {'==': {VProps.SUB_TYPE: NODE}},
                {'==': {VProps.TYPE: ALARM}},
            ]
        }
        subgraph = ga.graph_query_vertices(query_dict=query, depth=3)
        self.assertEqual(0, subgraph.num_edges(),
                         'num of BOTH edges Node (depth 3)')
        self.assertEqual(1, subgraph.num_vertex(),
                         'num of BOTH vertices Node (depth 3)')
