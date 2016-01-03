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

"""
test_vitrage graph
----------------------------------

Tests for `vitrage` graph driver
"""

from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import Direction
from vitrage.graph import utils
from vitrage.tests.unit.graph.base import *  # noqa


class GraphTest(GraphTestBase):

    def test_graph(self):
        g = create_graph('test_graph')
        self.assertEqual('test_graph', g.name, 'graph name')
        self.assertEqual(0, len(g), 'graph __len__')

        g.add_vertex(v_node)
        g.add_vertex(v_host)
        g.add_edge(e_node_to_host)
        self.assertEqual(2, len(g), 'graph __len__ after add vertices')

        graph_copy = g.copy()
        self.assertEqual('test_graph', graph_copy.name, 'graph copy name')
        self.assertEqual(2, len(graph_copy), 'graph copy __len__')

        g.remove_vertex(v_node)
        self.assertEqual(1, len(g), 'graph __len__ after remove vertex')
        self.assertEqual(2, len(graph_copy), 'graph copy __len__')

        updated_vertex = g.get_vertex(v_host.vertex_id)
        updated_vertex[VProps.TYPE] = ALARM
        g.update_vertex(updated_vertex)
        v_from_g = g.get_vertex(v_host.vertex_id)
        v_from_graph_copy = graph_copy.get_vertex(v_host.vertex_id)
        self.assertEqual(ALARM, v_from_g[VProps.TYPE],
                         'graph vertex changed after update')
        self.assertEqual(HOST, v_from_graph_copy[VProps.TYPE],
                         'graph copy vertex unchanged after update')

    def test_vertex_crud(self):
        g = create_graph('test_vertex_crud')
        g.add_vertex(v_node)
        v = g.get_vertex(v_node.vertex_id)
        self.assertEqual(v_node[VProps.ID], v[VProps.ID],
                         'vertex properties are saved')
        self.assertEqual(v_node[VProps.TYPE], v[VProps.TYPE],
                         'vertex properties are saved')
        self.assertEqual(v_node.vertex_id, v.vertex_id,
                         'vertex vertex_id is saved')

        # Changing the referenced item
        updated_v = v
        updated_v[VProps.SUB_TYPE] = 'KUKU'
        updated_v[VProps.TYPE] = 'CHANGED'
        # Get it again
        v = g.get_vertex(v_node.vertex_id)
        self.assertIsNone(v.get(VProps.SUB_TYPE, None),
                          'Change should not affect graph item')
        self.assertEqual(False, v.get(EProps.IS_DELETED, None),
                         'Change should not affect graph item')
        self.assertEqual(v_node[VProps.TYPE], v[VProps.TYPE],
                         'Change should not affect graph item')
        # Update the graph item and see changes take place
        g.update_vertex(updated_v)
        # Get it again
        v = g.get_vertex(v_node.vertex_id)
        self.assertEqual(updated_v[VProps.SUB_TYPE], v[VProps.SUB_TYPE],
                         'Graph item should change after update')
        self.assertEqual(updated_v[VProps.TYPE], v[VProps.TYPE],
                         'Graph item should change after update')

        # check metadata
        another_vertex = utils.create_vertex(
            vertex_id='123', entity_id='456', entity_type=INSTANCE,
            metadata={'some_meta': 'DATA'}
        )
        g.add_vertex(another_vertex)
        v = g.get_vertex(another_vertex.vertex_id)
        self.assertEqual(another_vertex[VProps.ID], v[VProps.ID],
                         'vertex properties are saved')
        self.assertEqual(another_vertex[VProps.TYPE], v[VProps.TYPE],
                         'vertex properties are saved')
        self.assertEqual('DATA', v['some_meta'],
                         'vertex properties are saved')
        self.assertEqual(another_vertex.vertex_id, v.vertex_id,
                         'vertex vertex_id is saved')

        # Remove the item
        g.remove_vertex(another_vertex)
        self.assertEqual(1, len(g), 'graph __len__ after remove vertex')
        v = g.get_vertex(another_vertex.vertex_id)
        self.assertIsNone(v, 'removed vertex not in graph')

    def test_edge_crud(self):
        g = create_graph('test_edge_crud')
        g.add_vertex(v_node)
        g.add_vertex(v_host)
        g.add_edge(e_node_to_host)
        self.assertEqual(1, g.num_edges(), 'graph __len__ after add edge')
        label = e_node_to_host[EProps.RELATION_NAME]
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertEqual(e_node_to_host[EProps.RELATION_NAME],
                         e[EProps.RELATION_NAME],
                         'edge properties are saved')
        self.assertEqual(e_node_to_host.source_id, e.source_id,
                         'edge vertex_id is saved')
        self.assertEqual(e_node_to_host.target_id, e.target_id,
                         'edge vertex_id is saved')

        # Edge is correct
        v_node_neig = g.neighbors(v_node.vertex_id, direction=Direction.OUT)
        self.assertEqual(1, len(v_node_neig),
                         'v_node OUT neighbor count')
        self.assertEqual(v_host.vertex_id, v_node_neig.pop().vertex_id,
                         'v_node OUT neighbor is v_host')
        v_node_neig = g.neighbors(v_node.vertex_id, direction=Direction.IN)
        self.assertEqual(0, len(v_node_neig),
                         'v_node IN neighbor count')
        v_host_neig = g.neighbors(v_host.vertex_id, direction=Direction.OUT)
        self.assertEqual(0, len(v_host_neig),
                         'v_host OUT neighbor count')
        v_host_neig = g.neighbors(v_host.vertex_id, direction=Direction.IN)
        self.assertEqual(1, len(v_host_neig),
                         'v_host IN neighbor count')
        self.assertEqual(v_node.vertex_id, v_host_neig.pop().vertex_id,
                         'v_host IN neighbor is v_node')

        # Changing the referenced item
        updated_e = e
        updated_e[EProps.IS_DELETED] = 'KUKU'
        updated_e[EProps.UPDATE_TIMESTAMP] = 'CHANGED'

        # Get it again
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertEqual(False, e.get(EProps.IS_DELETED, None),
                         'Change should not affect graph item')
        self.assertEqual(e_node_to_host[EProps.UPDATE_TIMESTAMP],
                         e[EProps.UPDATE_TIMESTAMP],
                         'Change should not affect graph item')
        # Update the graph item and see changes take place
        g.update_edge(updated_e)
        # Get it again
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertEqual(updated_e[EProps.IS_DELETED],
                         e[EProps.IS_DELETED],
                         'Graph item should change after update')
        self.assertEqual(updated_e[EProps.UPDATE_TIMESTAMP],
                         e[EProps.UPDATE_TIMESTAMP],
                         'Graph item should change after update')

        # check metadata
        another_label = 'ANOTHER_LABEL'
        another_edge = utils.create_edge(
            source_id=v_node.vertex_id,
            target_id=v_host.vertex_id,
            relation_type=another_label,
            metadata={'some_meta': 'DATA'})
        g.add_edge(another_edge)
        self.assertEqual(2, g.num_edges(), 'graph __len__ after add edge')
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, another_label)
        self.assertEqual(another_edge[EProps.RELATION_NAME],
                         e[EProps.RELATION_NAME],
                         'edge properties are saved')
        self.assertEqual('DATA', e['some_meta'],
                         'edge properties are saved')

        # Remove the item
        g.remove_edge(another_edge)
        self.assertEqual(1, g.num_edges(), 'graph __len__ after remove edge')
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, another_label)
        self.assertIsNone(e, 'removed edge not in graph')

        # Check get_edge returns None when item is missing
        edge = g.get_edge(v_host.vertex_id, 'ddd', '333')
        self.assertIsNone(edge)
        edge = g.get_edge('eee', v_node.vertex_id, '333')
        self.assertIsNone(edge)
        edge = g.get_edge(v_host.vertex_id, v_node.vertex_id, None)
        self.assertIsNone(edge)
        edge = g.get_edge(None, v_node.vertex_id, '333')
        self.assertIsNone(edge)

    def test_neighbors(self):
        relation_a = 'RELATION_A'
        relation_b = 'RELATION_B'
        relation_c = 'RELATION_C'

        v1 = v_node
        v2 = v_host
        v3 = v_instance
        v4 = v_alarm
        v5 = utils.create_vertex(
            vertex_id='kuku',
            entity_type=HOST)

        g = create_graph('test_neighbors')
        g.add_vertex(v1)
        g.add_vertex(v2)
        g.add_vertex(v3)
        g.add_vertex(v4)
        g.add_vertex(v5)

        g.add_edge(utils.create_edge(source_id=v1.vertex_id,
                                     target_id=v2.vertex_id,
                                     relation_type=relation_a))
        g.add_edge(utils.create_edge(source_id=v1.vertex_id,
                                     target_id=v2.vertex_id,
                                     relation_type=relation_b))
        g.add_edge(utils.create_edge(source_id=v1.vertex_id,
                                     target_id=v4.vertex_id,
                                     relation_type=relation_a))
        g.add_edge(utils.create_edge(source_id=v1.vertex_id,
                                     target_id=v4.vertex_id,
                                     relation_type=relation_b))
        g.add_edge(utils.create_edge(source_id=v2.vertex_id,
                                     target_id=v1.vertex_id,
                                     relation_type=relation_c))
        g.add_edge(utils.create_edge(source_id=v2.vertex_id,
                                     target_id=v3.vertex_id,
                                     relation_type=relation_a))
        g.add_edge(utils.create_edge(source_id=v2.vertex_id,
                                     target_id=v3.vertex_id,
                                     relation_type=relation_b))
        g.add_edge(utils.create_edge(source_id=v2.vertex_id,
                                     target_id=v4.vertex_id,
                                     relation_type=relation_a))
        g.add_edge(utils.create_edge(source_id=v4.vertex_id,
                                     target_id=v1.vertex_id,
                                     relation_type=relation_c))

        # CHECK V1

        v1_neighbors = g.neighbors(v_id=v1.vertex_id)
        self._assert_set_equal({v2, v4}, v1_neighbors, 'Check V1 neighbors')

        v1_neighbors = g.neighbors(
            v_id=v1.vertex_id,
            vertex_attr_filter={VProps.TYPE: HOST})
        self._assert_set_equal({v2}, v1_neighbors,
                               'Check V1 neighbors, vertex property filter')

        v1_neighbors = g.neighbors(
            v_id=v1.vertex_id,
            edge_attr_filter={EProps.RELATION_NAME: relation_a})
        self._assert_set_equal({v2, v4}, v1_neighbors,
                               'Check V1 neighbors, edge property filter')

        v1_neighbors = g.neighbors(v_id=v1.vertex_id,
                                   direction=Direction.IN)
        self._assert_set_equal({v2, v4}, v1_neighbors,
                               'Check V1 neighbors, direction IN')

        v1_neighbors = g.neighbors(v_id=v1.vertex_id,
                                   direction=Direction.OUT)
        self._assert_set_equal({v2, v4}, v1_neighbors,
                               'Check V1 neighbors, direction OUT')

        v1_neighbors = g.neighbors(v_id=v1.vertex_id,
                                   direction=Direction.BOTH)
        self._assert_set_equal({v2, v4}, v1_neighbors,
                               'Check V1 neighbors, direction BOTH')

        v1_neighbors = g.neighbors(
            v_id=v1.vertex_id,
            direction=Direction.IN,
            edge_attr_filter={EProps.RELATION_NAME: relation_c},
            vertex_attr_filter={VProps.TYPE: HOST})
        self._assert_set_equal(
            {v2}, v1_neighbors,
            'Check V1 neighbors, vertex/edge property filter and direction')

        # CHECK V2

        v2_neighbors = g.neighbors(v_id=v2.vertex_id)
        self._assert_set_equal({v1, v3, v4}, v2_neighbors,
                               'Check v2 neighbors')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            vertex_attr_filter={VProps.TYPE: HOST})
        self._assert_set_equal({}, v2_neighbors,
                               'Check v2 neighbors, vertex property filter')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            vertex_attr_filter={VProps.TYPE: [HOST, ALARM]})
        self._assert_set_equal({v4}, v2_neighbors,
                               'Check v2 neighbors, vertex property filter')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            edge_attr_filter={EProps.RELATION_NAME: [relation_a, relation_b]},
            vertex_attr_filter={VProps.TYPE: [HOST, ALARM, INSTANCE]})
        self._assert_set_equal({v3, v4}, v2_neighbors,
                               'Check v2 neighbors, edge property filter')

        # CHECK V3

        v3_neighbors = g.neighbors(v_id=v3.vertex_id, direction=Direction.OUT)
        self._assert_set_equal({}, v3_neighbors,
                               'Check v3 neighbors, direction OUT')

        v3_neighbors = g.neighbors(
            v_id=v3.vertex_id,
            vertex_attr_filter={VProps.TYPE: HOST},
            direction=Direction.OUT)
        self._assert_set_equal({}, v3_neighbors,
                               'Check neighbors for vertex without any')
        v5_neighbors = g.neighbors(
            v_id=v5.vertex_id,
            vertex_attr_filter={VProps.TYPE: HOST})
        self._assert_set_equal({}, v5_neighbors,
                               'Check neighbors for not connected vertex')
