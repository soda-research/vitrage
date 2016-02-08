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

import unittest

from vitrage.common.constants import SynchronizerProperties as SyncProps
from vitrage.common.constants import SyncMode
from vitrage.common.constants import VertexProperties
from vitrage.common.datetime_utils import utcnow
from vitrage.entity_graph.processor import processor as proc
from vitrage.tests import base
from vitrage.tests.mocks import mock_syncronizer as mock_sync


class TestProcessor(base.BaseTest):

    NUM_NODES = 1
    NUM_ZONES = 2
    NUM_HOSTS = 4
    NUM_INSTANCES = 15
    ZONE_SPEC = 'ZONE_SPEC'
    HOST_SPEC = 'HOST_SPEC'
    INSTANCE_SPEC = 'INSTANCE_SPEC'
    NUM_VERTICES_AFTER_CREATION = 2
    NUM_EDGES_AFTER_CREATION = 1
    NUM_VERTICES_AFTER_DELETION = 1
    NUM_EDGES_AFTER_DELETION = 0

    def setUp(self):
        super(TestProcessor, self).setUp()

    def test_create_entity_graph(self):
        processor = self._create_processor_with_graph()

        # check number of entities
        num_vertices = len(processor.entity_graph)
        self.assertEqual(self._num_resources_in_initial_graph(), num_vertices)

        # TODO(Alexey): add this check and to check also the number of edges
        # check all entities create a tree and no free floating vertices exists
        # it will be done only after we will have zone plugin
        # vertex = graph.find_vertex_in_graph()
        # bfs_list = graph.algo.bfs(graph)
        # self.assertEqual(num_vertices, len(bfs_list))

    # TODO(Alexey): un skip this test when instance transformer update is ready
    @unittest.skip('Not ready yet')
    def test_process_event(self):
        # check create instance event
        processor = proc.Processor()
        event = self._create_event(spec_type=self.INSTANCE_SPEC,
                                   sync_mode=SyncMode.INIT_SNAPSHOT)
        processor.process_event(event)
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)

        # check update instance even
        # TODO(Alexey): Create an event in update event structure
        # (update snapshot fields won't work)
        event[SyncProps.SYNC_MODE] = SyncMode.UPDATE
        event[SyncProps.EVENT_TYPE] = 'compute.instance.volume.attach'
        event['hostname'] = 'new_host'
        processor.process_event(event)
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)

        # check delete instance event
        event[SyncProps.SYNC_MODE] = SyncMode.UPDATE
        event[SyncProps.EVENT_TYPE] = 'compute.instance.delete.end'
        processor.process_event(event)
        self._check_graph(processor, self.NUM_VERTICES_AFTER_DELETION,
                          self.NUM_EDGES_AFTER_DELETION)

    def test_create_entity_with_placeholder_neighbor(self):
        # create instance event with host neighbor and check validity
        self._create_and_check_entity()

    def test_update_entity_state(self):
        # create instance event with host neighbor and check validity
        prop = {'status': 'STARTING'}
        (vertex, neighbors, processor) =\
            self._create_and_check_entity(properties=prop)

        # check added entity
        vertex = processor.entity_graph.get_vertex(vertex.vertex_id)
        self.assertEqual('STARTING', vertex.properties[VertexProperties.STATE])

        # update instance event with state running
        vertex.properties[VertexProperties.STATE] = 'RUNNING'
        vertex.properties[VertexProperties.UPDATE_TIMESTAMP] = str(utcnow())
        processor.update_entity(vertex, neighbors)

        # check state
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)
        vertex = processor.entity_graph.get_vertex(vertex.vertex_id)
        self.assertEqual('RUNNING', vertex.properties[VertexProperties.STATE])

    def test_change_parent(self):
        # create instance event with host neighbor and check validity
        (vertex, neighbors, processor) = self._create_and_check_entity()

        # update instance event with state running
        (neighbor_vertex, neighbor_edge) = neighbors[0]
        old_neighbor_id = neighbor_vertex.vertex_id
        neighbor_vertex.properties[VertexProperties.ID] = 'newhost-2'
        neighbor_vertex.vertex_id = 'RESOURCE_HOST_newhost-2'
        neighbor_edge.source_id = 'RESOURCE_HOST_newhost-2'
        processor.update_entity(vertex, neighbors)

        # check state
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)
        neighbor_vertex = \
            processor.entity_graph.get_vertex(old_neighbor_id)
        self.assertEqual(None, neighbor_vertex)

    def test_delete_entity(self):
        # create instance event with host neighbor and check validity
        (vertex, neighbors, processor) = self._create_and_check_entity()

        # delete entity
        processor.delete_entity(vertex, neighbors)

        # check deleted entity
        self._check_graph(processor, self.NUM_VERTICES_AFTER_DELETION,
                          self.NUM_EDGES_AFTER_DELETION)
        self.assertTrue(processor.entity_graph.is_vertex_deleted(vertex))

    def test_update_neighbors(self):
        # create instance event with host neighbor and check validity
        (vertex, neighbors, processor) = self._create_and_check_entity()

        # update instance event with state running
        (neighbor_vertex, neighbor_edge) = neighbors[0]
        old_neighbor_id = neighbor_vertex.vertex_id
        neighbor_vertex.properties[VertexProperties.ID] = 'newhost-2'
        neighbor_vertex.vertex_id = 'RESOURCE_HOST_newhost-2'
        neighbor_edge.source_id = 'RESOURCE_HOST_newhost-2'
        processor._update_neighbors(vertex, neighbors)

        # check state
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)
        self.assertEqual(None, processor.entity_graph.
                         get_vertex(old_neighbor_id))

        # update instance with the same neighbor
        processor._update_neighbors(vertex, neighbors)

        # check state
        self._check_graph(processor, self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)

    def test_delete_old_connections(self):
        # create instance event with host neighbor and check validity
        (vertex, neighbors, processor) = self._create_and_check_entity()

        # delete entity
        processor._delete_old_connections(vertex, [neighbors[0][1]])

        # check deleted entity
        self._check_graph(processor,
                          self.NUM_VERTICES_AFTER_DELETION,
                          self.NUM_EDGES_AFTER_DELETION)

    def _create_and_check_entity(self, properties={}):
        # create instance event with host neighbor
        (vertex, neighbors, processor) = self._create_entity(
            spec_type=self.INSTANCE_SPEC,
            sync_mode=SyncMode.INIT_SNAPSHOT,
            properties=properties)

        # check the data in the graph is correct
        self._check_graph(processor,
                          self.NUM_VERTICES_AFTER_CREATION,
                          self.NUM_EDGES_AFTER_CREATION)

        return vertex, neighbors, processor

    def _create_entity(self, processor=None, spec_type=None, sync_mode=None,
                       event_type=None, properties=None):
        # create instance event with host neighbor
        event = self._create_event(spec_type=spec_type,
                                   sync_mode=sync_mode,
                                   event_type=event_type,
                                   properties=properties)

        # add instance entity with host
        if processor is None:
            processor = proc.Processor()

        (vertex, neighbors, event_type) = processor.transform_entity(event)
        processor.create_entity(vertex, neighbors)

        return vertex, neighbors, processor

    def _check_graph(self, processor, num_vertices, num_edges):
        self.assertEqual(num_vertices, len(processor.entity_graph))
        self.assertEqual(num_edges, processor.entity_graph.num_edges())

    def _num_resources_in_initial_graph(self):
        return self.NUM_NODES + self.NUM_ZONES + \
            self.NUM_HOSTS + self.NUM_INSTANCES

    def _create_processor_with_graph(self):
        events = self._create_mock_events()
        processor = proc.Processor()

        for event in events:
            processor.process_event(event)

        return processor

    @staticmethod
    def _create_mock_events():
        gen_list = mock_sync.simple_zone_generators(
            2, 4, snapshot_events=2,
            snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        gen_list += mock_sync.simple_host_generators(
            2, 4, 4, snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        gen_list += mock_sync.simple_instance_generators(
            4, 15, 15, snap_vals={SyncProps.SYNC_MODE: SyncMode.INIT_SNAPSHOT})
        return mock_sync.generate_sequential_events_list(gen_list)

    def _create_event(self, spec_type=None, sync_mode=None,
                      event_type=None, properties=None):
        # generate event
        spec_list = mock_sync.simple_instance_generators(1, 1, 1)
        events_list = mock_sync.generate_random_events_list(
            spec_list)

        # update properties
        if sync_mode is not None:
            events_list[0][SyncProps.SYNC_MODE] = sync_mode

        if event_type is not None:
            events_list[0][SyncProps.EVENT_TYPE] = event_type

        if properties is not None:
            for key, value in properties.iteritems():
                events_list[0][key] = value

        return events_list[0]
