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
from vitrage.entity_graph.processor import entity_graph as entity_g
from vitrage.tests.unit.entity_graph.processor import base


class TestEntityGraphManager(base.TestBaseProcessor):

    @classmethod
    def setUpClass(cls):
        super(TestEntityGraphManager, cls).setUpClass()

    def test_can_vertex_be_deleted(self):
        entity_graph = entity_g.EntityGraph("Entity Graph")

        # create vertex properties
        instance_vertex = self._update_vertex_to_graph(entity_graph,
                                                       'RESOURCE', 'INSTANCE',
                                                       '123', False, True, {})

        # check is placeholder vertex
        is_placeholder_vertex = \
            entity_graph.can_vertex_be_deleted(instance_vertex)
        self.assertTrue(is_placeholder_vertex)

        # add host vertex
        host_vertex = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                                   'HOST', '321',
                                                   False, True, {})
        edge = self._update_edge_to_graph(entity_graph, host_vertex.vertex_id,
                                          instance_vertex.vertex_id,
                                          'contains')

        # check is placeholder vertex
        is_placeholder_vertex = \
            entity_graph.can_vertex_be_deleted(instance_vertex)
        self.assertFalse(is_placeholder_vertex)

        # change host to is_deleted
        entity_graph.mark_vertex_as_deleted(host_vertex)
        entity_graph.mark_edge_as_deleted(edge)

        # check is placeholder vertex
        is_placeholder_vertex = \
            entity_graph.can_vertex_be_deleted(instance_vertex)
        self.assertTrue(is_placeholder_vertex)

    def test_is_not_can_vertex_be_deleted(self):
        entity_graph = entity_g.EntityGraph("Entity Graph")

        # create vertex properties
        prop = {VertexProperties.STATE: 'ACTIVE'}
        vertex = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, False, prop)

        # check is not placeholder vertex
        is_placeholder_vertex = entity_graph.can_vertex_be_deleted(vertex)
        self.assertFalse(is_placeholder_vertex)

    def test_delete_placeholder_vertex(self):
        entity_graph = entity_g.EntityGraph("Entity Graph")

        # create vertex properties
        vertex = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, True, {})

        # check is placeholder vertex
        is_placeholder_vertex = entity_graph.can_vertex_be_deleted(vertex)
        self.assertTrue(is_placeholder_vertex)

        # deal with placeholder vertex - mark it as deleted
        entity_graph.delete_placeholder_vertex(vertex)
        vertex = entity_graph.get_vertex(vertex.vertex_id)
        self.assertTrue(not vertex)

    def test_mark_vertex_as_deleted(self):
        entity_graph = entity_g.EntityGraph("Entity Graph")

        # create vertex properties
        vertex = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                              'INSTANCE', '12345',
                                              False, True, {})

        # check vitrage deleted
        self.assertFalse(entity_graph.is_vertex_deleted(vertex))
        entity_graph.mark_vertex_as_deleted(vertex)
        self.assertTrue(entity_graph.is_vertex_deleted(vertex))

    def test_mark_edge_as_deleted(self):
        entity_graph = entity_g.EntityGraph("Entity Graph")

        # create vertex properties
        vertex1 = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                               'INSTANCE', '12345',
                                               False, True, {})
        vertex2 = self._update_vertex_to_graph(entity_graph, 'RESOURCE',
                                               'HOST', '54321',
                                               False, True, {})
        edge = self._update_edge_to_graph(entity_graph, vertex1.vertex_id,
                                          vertex2.vertex_id, 'contains')

        # check vitrage deleted
        self.assertFalse(entity_graph.is_edge_deleted(edge))
        entity_graph.mark_edge_as_deleted(edge)
        self.assertTrue(entity_graph.is_edge_deleted(edge))

    def test_find_neighbor_types(self):
        neighbors = []
        entity_graph = entity_g.EntityGraph("Entity Graph")
        entities_details = [('RESOURCE', 'HOST', '1', False, True),
                            ('RESOURCE', 'STORAGE', '2', False, True),
                            ('RESOURCE', 'APPLICATION', '3', False, True),
                            ('RESOURCE', 'STORAGE', '4', False, True),
                            ('ALARM', 'INSTANCE_AT_RISK', '5', False, True)]

        # add neighbors
        for details in entities_details:
            # neighbor
            vertex = self._update_vertex_to_graph(entity_graph, details[0],
                                                  details[1], details[2],
                                                  details[3], details[4], {})
            neighbors.append((vertex, None))

        # get neighbors types
        types = entity_graph.find_neighbor_types(neighbors)
        self.assertEqual(4, len(types))
