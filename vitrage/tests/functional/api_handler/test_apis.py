# Copyright 2016 - Nokia
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

import json

from vitrage.api_handler.apis.alarm import AlarmApis
from vitrage.api_handler.apis.rca import RcaApis
from vitrage.api_handler.apis.resource import ResourceApis
from vitrage.api_handler.apis.topology import TopologyApis
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import NOVA_ZONE_DATASOURCE
from vitrage.datasources.transformer_base \
    import create_cluster_placeholder_vertex
from vitrage.graph.driver.networkx_graph import NXGraph
import vitrage.graph.utils as graph_utils
from vitrage.tests.unit.entity_graph.base import TestEntityGraphUnitBase


class TestApis(TestEntityGraphUnitBase):

    def test_get_alarms_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants=False)
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(3, len(alarms))
        self._check_projects_entities(alarms, 'project_1', True)

    def test_get_alarms_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants=False)
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(2, len(alarms))
        self._check_projects_entities(alarms, 'project_2', True)

    def test_get_alarms_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = AlarmApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        alarms = apis.get_alarms(ctx, vitrage_id='all', all_tenants=True)
        alarms = json.loads(alarms)['alarms']

        # Test assertions
        self.assertEqual(5, len(alarms))
        self._check_projects_entities(alarms, None, True)

    def test_get_rca_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants=False)
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(3, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_1', True)

    def test_get_rca_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx,
                                 root='alarm_on_instance_3',
                                 all_tenants=False)
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(2, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_2', True)

    def test_get_rca_with_not_admin_bla_project(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants=False)
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(3, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], 'project_2', True)

    def test_get_rca_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = RcaApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        graph_rca = apis.get_rca(ctx, root='alarm_on_host', all_tenants=True)
        graph_rca = json.loads(graph_rca)

        # Test assertions
        self.assertEqual(5, len(graph_rca['nodes']))
        self._check_projects_entities(graph_rca['nodes'], None, True)

    def test_get_topology_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root=None,
            all_tenants=False)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(8, len(graph_topology['nodes']))
        self._check_projects_entities(graph_topology['nodes'],
                                      'project_1',
                                      False)

    def test_get_topology_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root=None,
            all_tenants=False)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(7, len(graph_topology['nodes']))
        self._check_projects_entities(graph_topology['nodes'],
                                      'project_2',
                                      False)

    def test_get_topology_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = TopologyApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        graph_topology = apis.get_topology(
            ctx,
            graph_type='graph',
            depth=10,
            query=None,
            root=None,
            all_tenants=True)
        graph_topology = json.loads(graph_topology)

        # Test assertions
        self.assertEqual(12, len(graph_topology['nodes']))

    def test_resource_list_with_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': True}

        # Action
        resources = apis.get_resources(
            ctx,
            resource_type=None,
            all_tenants=False)
        resources = json.loads(resources)['resources']

        # Test assertions
        self.assertEqual(5, len(resources))

    def test_resource_list_with_not_admin_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        resources = apis.get_resources(
            ctx,
            resource_type=None,
            all_tenants=False)
        resources = json.loads(resources)['resources']

        # Test assertions
        self.assertEqual(2, len(resources))

    def test_resource_list_with_not_admin_project_and_no_existing_type(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        resources = apis.get_resources(
            ctx,
            resource_type=NOVA_HOST_DATASOURCE,
            all_tenants=False)
        resources = json.loads(resources)['resources']

        # Test assertions
        self.assertEqual(0, len(resources))

    def test_resource_list_with_not_admin_project_and_existing_type(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        resources = apis.get_resources(
            ctx,
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=False)
        resources = json.loads(resources)['resources']

        # Test assertions
        self.assertEqual(2, len(resources))

    def test_resource_list_with_all_tenants(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        resources = apis.get_resources(
            ctx,
            resource_type=None,
            all_tenants=True)
        resources = json.loads(resources)['resources']

        # Test assertions
        self.assertEqual(7, len(resources))

    def test_resource_show_with_admin_and_no_project_resource(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        resource = apis.show_resource(ctx, 'zone_1')
        resource = json.loads(resource)

        # Test assertions
        self.assertIsNotNone(resource)
        self._check_resource_propeties(resource, 'zone_1',
                                       NOVA_ZONE_DATASOURCE)

    def test_resource_show_with_not_admin_and_no_project_resource(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        resource = apis.show_resource(ctx, 'zone_1')

        # Test assertions
        self.assertIsNone(resource)

    def test_resource_show_with_not_admin_and_resource_in_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': False}

        # Action
        resource = apis.show_resource(ctx, 'instance_2')
        resource = json.loads(resource)

        # Test assertions
        self.assertIsNotNone(resource)
        self._check_resource_propeties(resource, 'instance_2',
                                       NOVA_INSTANCE_DATASOURCE,
                                       project_id='project_1')

    def test_resource_show_with_not_admin_and_resource_in_other_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': False}

        # Action
        resource = apis.show_resource(ctx, 'instance_2')

        # Test assertions
        self.assertIsNone(resource)

    def test_resource_show_with_admin_and_resource_in_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_1', 'is_admin': True}

        # Action
        resource = apis.show_resource(ctx, 'instance_2')
        resource = json.loads(resource)

        # Test assertions
        self.assertIsNotNone(resource)
        self._check_resource_propeties(resource, 'instance_2',
                                       NOVA_INSTANCE_DATASOURCE,
                                       project_id='project_1')

    def test_resource_show_with_admin_and_resource_in_other_project(self):
        # Setup
        graph = self._create_graph()
        apis = ResourceApis(graph, None)
        ctx = {'tenant': 'project_2', 'is_admin': True}

        # Action
        resource = apis.show_resource(ctx, 'instance_2')
        resource = json.loads(resource)

        # Test assertions
        self.assertIsNotNone(resource)
        self._check_resource_propeties(resource, 'instance_2',
                                       NOVA_INSTANCE_DATASOURCE,
                                       project_id='project_1')

    def _check_projects_entities(self,
                                 alarms,
                                 project_id,
                                 check_alarm_category):
        for alarm in alarms:
            tmp_project_id = alarm.get(VProps.PROJECT_ID, None)
            condition = True
            if check_alarm_category:
                condition = alarm[VProps.CATEGORY] == EntityCategory.ALARM
            if project_id:
                condition = condition and \
                    (not tmp_project_id or
                     (tmp_project_id and tmp_project_id == project_id))
            self.assertEqual(True, condition)

    def _check_resource_propeties(self, resource, vitrage_id,
                                  resource_type, project_id=None):
        self.assertEqual(resource[VProps.VITRAGE_ID], vitrage_id)
        self.assertEqual(resource[VProps.ID], vitrage_id)
        self.assertEqual(resource[VProps.CATEGORY], EntityCategory.RESOURCE)
        self.assertEqual(resource[VProps.TYPE], resource_type)
        self.assertEqual(resource[VProps.STATE], 'active')
        self.assertFalse(resource[VProps.IS_DELETED])
        self.assertFalse(resource[VProps.IS_PLACEHOLDER])
        if project_id:
            self.assertEqual(resource[VProps.PROJECT_ID], project_id)

    def _create_graph(self):
        graph = NXGraph('Multi tenancy graph', uuid=True)

        # create vertices
        cluster_vertex = create_cluster_placeholder_vertex()
        zone_vertex = self._create_resource('zone_1',
                                            NOVA_ZONE_DATASOURCE)
        host_vertex = self._create_resource('host_1',
                                            NOVA_HOST_DATASOURCE)
        instance_1_vertex = self._create_resource('instance_1',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_1')
        instance_2_vertex = self._create_resource('instance_2',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_1')
        instance_3_vertex = self._create_resource('instance_3',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_2')
        instance_4_vertex = self._create_resource('instance_4',
                                                  NOVA_INSTANCE_DATASOURCE,
                                                  project_id='project_2')
        alarm_on_host_vertex = self._create_alarm(
            'alarm_on_host',
            'alarm_on_host',
            metadata={'type': 'nova.host',
                      'name': 'host_1',
                      'resource_id': 'host_1'})
        alarm_on_instance_1_vertex = self._create_alarm(
            'alarm_on_instance_1',
            'deduced_alarm',
            project_id='project_1',
            metadata={'type': 'nova.instance',
                      'name': 'instance_1',
                      'resource_id': 'sdg7849ythksjdg'})
        alarm_on_instance_2_vertex = self._create_alarm(
            'alarm_on_instance_2',
            'deduced_alarm',
            metadata={'type': 'nova.instance',
                      'name': 'instance_2',
                      'resource_id': 'nbfhsdugf'})
        alarm_on_instance_3_vertex = self._create_alarm(
            'alarm_on_instance_3',
            'deduced_alarm',
            project_id='project_2',
            metadata={'type': 'nova.instance',
                      'name': 'instance_3',
                      'resource_id': 'nbffhsdasdugf'})
        alarm_on_instance_4_vertex = self._create_alarm(
            'alarm_on_instance_4',
            'deduced_alarm',
            metadata={'type': 'nova.instance',
                      'name': 'instance_4',
                      'resource_id': 'ngsuy76hgd87f'})

        # create links
        edges = list()
        edges.append(graph_utils.create_edge(
            cluster_vertex.vertex_id,
            zone_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            zone_vertex.vertex_id,
            host_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_1_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_2_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_3_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            host_vertex.vertex_id,
            instance_4_vertex.vertex_id,
            'contains'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            host_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_1_vertex.vertex_id,
            instance_1_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_2_vertex.vertex_id,
            instance_2_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_3_vertex.vertex_id,
            instance_3_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_instance_4_vertex.vertex_id,
            instance_4_vertex.vertex_id,
            'on'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_1_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_2_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_3_vertex.vertex_id,
            'causes'))
        edges.append(graph_utils.create_edge(
            alarm_on_host_vertex.vertex_id,
            alarm_on_instance_4_vertex.vertex_id,
            'causes'))

        # add vertices to graph
        graph.add_vertex(cluster_vertex)
        graph.add_vertex(zone_vertex)
        graph.add_vertex(host_vertex)
        graph.add_vertex(instance_1_vertex)
        graph.add_vertex(instance_2_vertex)
        graph.add_vertex(instance_3_vertex)
        graph.add_vertex(instance_4_vertex)
        graph.add_vertex(alarm_on_host_vertex)
        graph.add_vertex(alarm_on_instance_1_vertex)
        graph.add_vertex(alarm_on_instance_2_vertex)
        graph.add_vertex(alarm_on_instance_3_vertex)
        graph.add_vertex(alarm_on_instance_4_vertex)

        # add links to graph
        for edge in edges:
            graph.add_edge(edge)

        return graph
