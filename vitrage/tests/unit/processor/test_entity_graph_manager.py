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

from vitrage.common.constants import VertexProperties
from vitrage.entity_graph.processor import entity_graph_manager
from vitrage.tests.unit.processor import base


class TestEntityGraphManager(base.BaseProcessor):

    def setUp(self):
        super(TestEntityGraphManager, self).setUp()

    def test_is_partial_data_vertex(self):
        e_g_manager = entity_graph_manager.EntityGraphManager()

        # create vertex properties
        instance_vertex = self._update_vertex_to_graph(e_g_manager,
                                                       'RESOURCE', 'INSTANCE',
                                                       '123', False, True, {})

        # check is partial data vertex
        is_partial_data_vertex = \
            e_g_manager.is_partial_data_vertex(instance_vertex)
        self.assertTrue(is_partial_data_vertex)

        # add host vertex
        host_vertex = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                                   'HOST', '321',
                                                   False, True, {})
        edge = self._update_edge_to_graph(e_g_manager, host_vertex.vertex_id,
                                          instance_vertex.vertex_id,
                                          'contains')

        # check is partial data vertex
        is_partial_data_vertex = \
            e_g_manager.is_partial_data_vertex(instance_vertex)
        self.assertFalse(is_partial_data_vertex)

        # change host to is_deleted
        e_g_manager.mark_vertex_as_deleted(host_vertex)
        e_g_manager.mark_edge_as_deleted(edge)

        # check is partial data vertex
        is_partial_data_vertex = \
            e_g_manager.is_partial_data_vertex(instance_vertex)
        self.assertTrue(is_partial_data_vertex)

    def test_is_not_partial_data_vertex(self):
        e_g_manager = entity_graph_manager.EntityGraphManager()

        # create vertex properties
        prop = {VertexProperties.STATE: 'ACTIVE'}
        vertex = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, False, prop)

        # check is not partial data vertex
        is_partial_data_vertex = e_g_manager.is_partial_data_vertex(vertex)
        self.assertFalse(is_partial_data_vertex)

    def test_delete_partial_data_vertex(self):
        e_g_manager = entity_graph_manager.EntityGraphManager()

        # create vertex properties
        vertex = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, True, {})

        # check is partial data vertex
        is_partial_data_vertex = e_g_manager.is_partial_data_vertex(vertex)
        self.assertTrue(is_partial_data_vertex)

        # deal with partial data vertex - mark it as deleted
        e_g_manager.delete_partial_data_vertex(vertex)
        vertex = e_g_manager.graph.get_vertex(vertex.vertex_id)
        self.assertTrue(not vertex)

    def test_mark_vertex_as_deleted(self):
        e_g_manager = entity_graph_manager.EntityGraphManager()

        # create vertex properties
        vertex = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, True, {})

        # check vitrage deleted
        self.assertFalse(e_g_manager.is_vertex_deleted(vertex))
        e_g_manager.mark_vertex_as_deleted(vertex)
        self.assertTrue(e_g_manager.is_vertex_deleted(vertex))

    def test_mark_edge_as_deleted(self):
        e_g_manager = entity_graph_manager.EntityGraphManager()

        # create vertex properties
        vertex1 = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                               'INSTANCE', '12345',
                                               False, True, {})
        vertex2 = self._update_vertex_to_graph(e_g_manager, 'RESOURCE',
                                               'HOST', '54321',
                                               False, True, {})
        edge = self._update_edge_to_graph(e_g_manager, vertex1.vertex_id,
                                          vertex2.vertex_id, 'contains')

        # check vitrage deleted
        self.assertFalse(e_g_manager.is_edge_deleted(edge))
        e_g_manager.mark_edge_as_deleted(edge)
        self.assertTrue(e_g_manager.is_edge_deleted(edge))

    def test_find_neighbor_types(self):
        neighbors = []
        e_g_manager = entity_graph_manager.EntityGraphManager()
        entities_details = [('RESOURCE', 'HOST', '1', False, True),
                            ('RESOURCE', 'STORAGE', '2', False, True),
                            ('RESOURCE', 'APPLICATION', '3', False, True),
                            ('RESOURCE', 'STORAGE', '4', False, True),
                            ('ALARM', 'INSTANCE_AT_RISK', '5', False, True)]

        # add neighbors
        for details in entities_details:
            # neighbor
            vertex = self._update_vertex_to_graph(e_g_manager, details[0],
                                                  details[1], details[2],
                                                  details[3], details[4], {})
            neighbors.append((vertex, None))

        # get neighbors types
        types = e_g_manager.find_neighbor_types(neighbors)
        self.assertEqual(4, len(types))
