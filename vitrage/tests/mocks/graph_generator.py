# Copyright 2018 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import itertools

from vitrage.common.constants import EdgeProperties
from vitrage.graph import Direction
from vitrage.graph.driver.networkx_graph import NXGraph
from vitrage.graph import Edge
from vitrage.graph import Vertex
from vitrage.tests.mocks import utils

RESOURCES_PATH = utils.get_resources_dir() + '/mock_configurations'


class GraphGenerator(object):
    def __init__(self,
                 num_of_networks=2,
                 num_of_zones_per_cluster=2,
                 num_of_hosts_per_zone=2,
                 num_of_zabbix_alarms_per_host=2,
                 num_of_instances_per_host=2,
                 num_of_ports_per_instance=2,
                 num_of_volumes_per_instance=2,
                 num_of_vitrage_alarms_per_instance=2,
                 num_of_tripleo_controllers=2,
                 num_of_zabbix_alarms_per_controller=2):
        self.id_counter = 0
        self._num_of_networks = num_of_networks
        self._num_of_zones_per_cluster = num_of_zones_per_cluster
        self._num_of_hosts_per_zone = num_of_hosts_per_zone
        self._num_of_zabbix_alarms_per_host = num_of_zabbix_alarms_per_host
        self._num_of_instances_per_host = num_of_instances_per_host
        self._num_of_ports_per_instance = num_of_ports_per_instance
        self._num_of_volumes_per_instance = num_of_volumes_per_instance
        self._num_of_vitrage_alarms_per_instance = \
            num_of_vitrage_alarms_per_instance
        self._num_of_tripleo_controllers = num_of_tripleo_controllers
        self._num_of_zabbix_alarms_per_controller = \
            num_of_zabbix_alarms_per_controller

    def create_graph(self):
        graph = NXGraph()
        v1 = self._file_to_vertex('openstack-cluster.json')
        graph.add_vertex(v1)

        networks = self._create_n_vertices(graph,
                                           self._num_of_networks,
                                           'neutron.network.json')
        zones = self._create_n_neighbors(graph,
                                         self._num_of_zones_per_cluster,
                                         [v1],
                                         'nova.zone.json',
                                         'contains.json')
        hosts = self._create_n_neighbors(graph,
                                         self._num_of_hosts_per_zone,
                                         zones,
                                         'nova.host.json',
                                         'contains.json')
        self._create_n_neighbors(graph,
                                 self._num_of_zabbix_alarms_per_host,
                                 hosts,
                                 'zabbix.json',
                                 'on.json',
                                 Direction.IN)
        instances = self._create_n_neighbors(graph,
                                             self._num_of_instances_per_host,
                                             hosts,
                                             'nova.instance.json',
                                             'contains.json')
        ports = self._create_n_neighbors(graph,
                                         self._num_of_ports_per_instance,
                                         instances,
                                         'neutron.port.json',
                                         'attached.json',
                                         direction=Direction.IN)

        self._round_robin_edges(graph, networks, ports, 'contains.json')

        self._create_n_neighbors(graph,
                                 self._num_of_volumes_per_instance,
                                 instances,
                                 'cinder.volume.json',
                                 'attached.json',
                                 Direction.IN)
        self._create_n_neighbors(graph,
                                 self._num_of_vitrage_alarms_per_instance,
                                 instances,
                                 'vitrage.alarm.json',
                                 'on.json',
                                 Direction.IN)

        # Also create non connected components:
        tripleo_controller = \
            self._create_n_vertices(graph,
                                    self._num_of_tripleo_controllers,
                                    'tripleo.controller.json')
        self._create_n_neighbors(graph,
                                 self._num_of_zabbix_alarms_per_controller,
                                 tripleo_controller,
                                 'zabbix.json',
                                 'on.json',
                                 Direction.IN)
        return graph

    def _create_n_vertices(self, g, n, props_file):
        created_vertices = []
        for i in range(n):
            v = self._file_to_vertex(props_file)
            created_vertices.append(v)
            g.add_vertex(v)
        return created_vertices

    def _create_n_neighbors(self, g, n, source_v_list,
                            neighbor_props_file, neighbor_edge_props_file,
                            direction=Direction.OUT):
        created_vertices = []
        for source_v in source_v_list:
            for i in range(n):
                v = self._file_to_vertex(neighbor_props_file)
                created_vertices.append(v)
                g.add_vertex(v)
                if direction == Direction.OUT:
                    g.add_edge(self._file_to_edge(neighbor_edge_props_file,
                                                  source_v.vertex_id,
                                                  v.vertex_id))
                else:
                    g.add_edge(
                        self._file_to_edge(neighbor_edge_props_file,
                                           v.vertex_id,
                                           source_v.vertex_id))
        return created_vertices

    def _round_robin_edges(self,
                           graph,
                           source_vertices,
                           target_vertices,
                           edge_props_file):
        round_robin_source_vertices = itertools.cycle(source_vertices)
        for v in target_vertices:
            source_v = next(round_robin_source_vertices)
            graph.add_edge(self._file_to_edge(edge_props_file,
                                              source_v.vertex_id,
                                              v.vertex_id))

    def _file_to_vertex(self, relative_path):
        full_path = RESOURCES_PATH + "/vertices/"
        props = utils.load_specs(relative_path, full_path)
        v = Vertex(str(self.id_counter), props)
        self.id_counter += 1
        return v

    @staticmethod
    def _file_to_edge(relative_path, source_id, target_id):
        full_path = RESOURCES_PATH + "/edges/"
        props = utils.load_specs(relative_path, full_path)
        return Edge(source_id, target_id,
                    props[EdgeProperties.RELATIONSHIP_TYPE],
                    props)
