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
from oslo_log import log as logging

import random
import time

from vitrage.common.constants import EdgeConstants as EConst
from vitrage.common.constants import EdgeLabels as ELabel
from vitrage.common.constants import VertexConstants as VConst
from vitrage.graph import create_graph
from vitrage.graph import Direction
from vitrage.graph import util
from vitrage.tests.unit import base

LOG = logging.getLogger(__name__)

ENTITY_GRAPH_HOSTS_PER_NODE = 32
ENTITY_GRAPH_VMS_PER_HOST = 32
ENTITY_GRAPH_ALARMS_PER_HOST = 8
ENTITY_GRAPH_ALARMS_PER_VM = 8

ALARM = 'ALARM'
HOST = 'HOST'
INSTANCE = 'INSTANCE'
NODE = 'NODE'

v_node = util.create_vertex(
    vertex_id=NODE + '111111111111',
    entity_id='111111111111',
    entity_type=NODE)
v_host = util.create_vertex(
    vertex_id=HOST + '222222222222',
    entity_id='222222222222',
    entity_type=HOST)
v_instance = util.create_vertex(
    vertex_id=INSTANCE + '333333333333',
    entity_id='333333333333',
    entity_type=INSTANCE)
v_alarm = util.create_vertex(
    vertex_id=ALARM + '444444444444',
    entity_id='444444444444',
    entity_type=ALARM)

e_node_to_host = util.create_edge(
    source_id=v_node.vertex_id,
    target_id=v_host.vertex_id,
    relation_type=ELabel.CONTAINS,
    deletion_timestamp='123')


def add_connected_vertex(entity_type, edge_type, graph, id, other_vertex):
    host_to_add = util.create_vertex(
        vertex_id=entity_type + str(id),
        entity_id=id,
        entity_type=entity_type)
    edge_to_add = util.create_edge(
        source_id=host_to_add.vertex_id,
        target_id=other_vertex.vertex_id,
        relation_type=edge_type)
    graph.add_vertex(host_to_add)
    graph.add_edge(edge_to_add)
    return host_to_add


def rand_vertex_id(entity_type, items_count, max_id):
    random_vm_entity_id = random.randint(
        max_id - items_count, max_id - 1)
    vertex_id = entity_type + str(random_vm_entity_id)
    return vertex_id


def create_entity_graph(name, num_of_alarms_per_host,
                        num_of_alarms_per_vm,
                        num_of_hosts_per_node,
                        num_of_vms_per_host):
    vms = []
    vm_id = 10000000
    host_alarm_id = 20000000
    vm_alarm_id = 30000000
    start = time.time()
    g = create_graph(name)
    g.add_vertex(v_node)

    # Add Hosts
    for i in xrange(num_of_hosts_per_node):
        host_to_add = add_connected_vertex(HOST, ELabel.CONTAINS,
                                           g, i, v_node)

        # Add Host Alarms
        for j in xrange(num_of_alarms_per_host):
            add_connected_vertex(ALARM, ELabel.ON, g, host_alarm_id,
                                 host_to_add)
            host_alarm_id += 1

        # Add Host Vms
        for j in xrange(num_of_vms_per_host):
            vm_to_add = add_connected_vertex(INSTANCE, ELabel.CONTAINS, g,
                                             vm_id, host_to_add)
            vm_id += 1
            vms.append(vm_to_add)

            # Add Instance Alarms
            for k in xrange(num_of_alarms_per_vm):
                add_connected_vertex(ALARM, ELabel.ON, g, vm_alarm_id,
                                     vm_to_add)
                vm_alarm_id += 1

    end = time.time()
    LOG.debug('Graph creation took ' + str(end - start) +
              ' seconds, size is: ' + str(len(g)))
    expected_graph_size = \
        1 + num_of_hosts_per_node + num_of_hosts_per_node * \
        num_of_alarms_per_host + num_of_hosts_per_node * \
        num_of_vms_per_host + num_of_hosts_per_node * \
        num_of_vms_per_host * num_of_alarms_per_vm
    assert expected_graph_size == len(g), 'Graph size'
    return g, vm_alarm_id, vm_id, vms

entity_graph, vm_alarm_id, vm_id, vms = create_entity_graph(
    'entity_graph',
    num_of_hosts_per_node=ENTITY_GRAPH_HOSTS_PER_NODE,
    num_of_vms_per_host=ENTITY_GRAPH_VMS_PER_HOST,
    num_of_alarms_per_host=ENTITY_GRAPH_ALARMS_PER_HOST,
    num_of_alarms_per_vm=ENTITY_GRAPH_ALARMS_PER_VM)


class GraphTest(base.BaseTest):

    def _assert_set_equal(self, d1, d2, message):
        super(GraphTest, self).assert_dict_equal(dict(d1), dict(d2), message)

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
        updated_vertex[VConst.TYPE] = ALARM
        g.update_vertex(updated_vertex)
        v_from_g = g.get_vertex(v_host.vertex_id)
        v_from_graph_copy = graph_copy.get_vertex(v_host.vertex_id)
        self.assertEqual(ALARM, v_from_g[VConst.TYPE],
                         'graph vertex changed after update')
        self.assertEqual(HOST, v_from_graph_copy[VConst.TYPE],
                         'graph copy vertex unchanged after update')

    def test_vertex_crud(self):
        g = create_graph('test_vertex_crud')
        g.add_vertex(v_node)
        v = g.get_vertex(v_node.vertex_id)
        self.assertEqual(v_node[VConst.ID], v[VConst.ID],
                         'vertex properties are saved')
        self.assertEqual(v_node[VConst.TYPE], v[VConst.TYPE],
                         'vertex properties are saved')
        self.assertEqual(v_node.vertex_id, v.vertex_id,
                         'vertex vertex_id is saved')

        # Changing the referenced item
        updated_v = v
        updated_v[VConst.SUB_TYPE] = 'KUKU'
        updated_v[VConst.TYPE] = 'CHANGED'
        # Get it again
        v = g.get_vertex(v_node.vertex_id)
        self.assertIsNone(v.get(VConst.SUB_TYPE, None),
                          'Change should not affect graph item')
        self.assertEqual(v_node[VConst.TYPE], v[VConst.TYPE],
                         'Change should not affect graph item')
        # Update the graph item and see changes take place
        g.update_vertex(updated_v)
        # Get it again
        v = g.get_vertex(v_node.vertex_id)
        self.assertEqual(updated_v[VConst.SUB_TYPE], v[VConst.SUB_TYPE],
                         'Graph item should change after update')
        self.assertEqual(updated_v[VConst.TYPE], v[VConst.TYPE],
                         'Graph item should change after update')

        # check metadata
        another_vertex = util.create_vertex(
            vertex_id='123', entity_id='456', entity_type=INSTANCE,
            metadata={'some_meta': 'DATA'}
        )
        g.add_vertex(another_vertex)
        v = g.get_vertex(another_vertex.vertex_id)
        self.assertEqual(another_vertex[VConst.ID], v[VConst.ID],
                         'vertex properties are saved')
        self.assertEqual(another_vertex[VConst.TYPE], v[VConst.TYPE],
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
        label = e_node_to_host[EConst.RELATION_NAME]
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertEqual(e_node_to_host[EConst.RELATION_NAME],
                         e[EConst.RELATION_NAME],
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
        updated_e[EConst.IS_EDGE_DELETED] = 'KUKU'
        updated_e[EConst.EDGE_DELETION_TIMESTAMP] = 'CHANGED'

        # Get it again
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertIsNone(e.get(EConst.IS_EDGE_DELETED, None),
                          'Change should not affect graph item')
        self.assertEqual(e_node_to_host[EConst.EDGE_DELETION_TIMESTAMP],
                         e[EConst.EDGE_DELETION_TIMESTAMP],
                         'Change should not affect graph item')
        # Update the graph item and see changes take place
        g.update_edge(updated_e)
        # Get it again
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, label)
        self.assertEqual(updated_e[EConst.IS_EDGE_DELETED],
                         e[EConst.IS_EDGE_DELETED],
                         'Graph item should change after update')
        self.assertEqual(updated_e[EConst.EDGE_DELETION_TIMESTAMP],
                         e[EConst.EDGE_DELETION_TIMESTAMP],
                         'Graph item should change after update')

        # check metadata
        another_label = 'ANOTHER_LABEL'
        another_edge = util.create_edge(
            source_id=v_node.vertex_id,
            target_id=v_host.vertex_id,
            relation_type=another_label,
            metadata={'some_meta': 'DATA'})
        g.add_edge(another_edge)
        self.assertEqual(2, g.num_edges(), 'graph __len__ after add edge')
        e = g.get_edge(v_node.vertex_id, v_host.vertex_id, another_label)
        self.assertEqual(another_edge[EConst.RELATION_NAME],
                         e[EConst.RELATION_NAME],
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
        v5 = util.create_vertex(
            vertex_id='kuku',
            entity_type=HOST)

        g = create_graph('test_neighbors')
        g.add_vertex(v1)
        g.add_vertex(v2)
        g.add_vertex(v3)
        g.add_vertex(v4)
        g.add_vertex(v5)

        g.add_edge(util.create_edge(source_id=v1.vertex_id,
                                    target_id=v2.vertex_id,
                                    relation_type=relation_a))
        g.add_edge(util.create_edge(source_id=v1.vertex_id,
                                    target_id=v2.vertex_id,
                                    relation_type=relation_b))
        g.add_edge(util.create_edge(source_id=v1.vertex_id,
                                    target_id=v4.vertex_id,
                                    relation_type=relation_a))
        g.add_edge(util.create_edge(source_id=v1.vertex_id,
                                    target_id=v4.vertex_id,
                                    relation_type=relation_b))
        g.add_edge(util.create_edge(source_id=v2.vertex_id,
                                    target_id=v1.vertex_id,
                                    relation_type=relation_c))
        g.add_edge(util.create_edge(source_id=v2.vertex_id,
                                    target_id=v3.vertex_id,
                                    relation_type=relation_a))
        g.add_edge(util.create_edge(source_id=v2.vertex_id,
                                    target_id=v3.vertex_id,
                                    relation_type=relation_b))
        g.add_edge(util.create_edge(source_id=v2.vertex_id,
                                    target_id=v4.vertex_id,
                                    relation_type=relation_a))
        g.add_edge(util.create_edge(source_id=v4.vertex_id,
                                    target_id=v1.vertex_id,
                                    relation_type=relation_c))

        # CHECK V1

        v1_neighbors = g.neighbors(v_id=v1.vertex_id)
        self._assert_set_equal({v2, v4}, v1_neighbors, 'Check V1 neighbors')

        v1_neighbors = g.neighbors(
            v_id=v1.vertex_id,
            vertex_attr_filter={VConst.TYPE: HOST})
        self._assert_set_equal({v2}, v1_neighbors,
                               'Check V1 neighbors, vertex property filter')

        v1_neighbors = g.neighbors(
            v_id=v1.vertex_id,
            edge_attr_filter={EConst.RELATION_NAME: relation_a})
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
            edge_attr_filter={EConst.RELATION_NAME: relation_c},
            vertex_attr_filter={VConst.TYPE: HOST})
        self._assert_set_equal(
            {v2}, v1_neighbors,
            'Check V1 neighbors, vertex/edge property filter and direction')

        # CHECK V2

        v2_neighbors = g.neighbors(v_id=v2.vertex_id)
        self._assert_set_equal({v1, v3, v4}, v2_neighbors,
                               'Check v2 neighbors')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            vertex_attr_filter={VConst.TYPE: HOST})
        self._assert_set_equal({}, v2_neighbors,
                               'Check v2 neighbors, vertex property filter')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            vertex_attr_filter={VConst.TYPE: [HOST, ALARM]})
        self._assert_set_equal({v4}, v2_neighbors,
                               'Check v2 neighbors, vertex property filter')

        v2_neighbors = g.neighbors(
            v_id=v2.vertex_id,
            edge_attr_filter={EConst.RELATION_NAME: [relation_a, relation_b]},
            vertex_attr_filter={VConst.TYPE: [HOST, ALARM, INSTANCE]})
        self._assert_set_equal({v3, v4}, v2_neighbors,
                               'Check v2 neighbors, edge property filter')

        # CHECK V3

        v3_neighbors = g.neighbors(v_id=v3.vertex_id)
        self._assert_set_equal({}, v3_neighbors,
                               'Check v3 neighbors, direction OUT')

        v3_neighbors = g.neighbors(
            v_id=v3.vertex_id,
            vertex_attr_filter={VConst.TYPE: HOST})
        self._assert_set_equal({}, v3_neighbors,
                               'Check neighbors for vertex without any')
        v5_neighbors = g.neighbors(
            v_id=v5.vertex_id,
            vertex_attr_filter={VConst.TYPE: HOST})
        self._assert_set_equal({}, v5_neighbors,
                               'Check neighbors for not connected vertex')
