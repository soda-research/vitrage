# Copyright 2018 - Nokia, ZTE
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR  CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import json

from oslo_log import log


from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.static.driver import StaticDriver
from vitrage.datasources.static import StaticFields
from vitrage.tests.mocks.graph_generator import GraphGenerator
from vitrage.tests.mocks.mock_graph_datasource import MOCK_DATASOURCE

LOG = log.getLogger(__name__)


class MockDriver(StaticDriver):

    e_graph = GraphGenerator(
        num_of_networks=2,
        num_of_zones_per_cluster=2,
        num_of_hosts_per_zone=64,
        num_of_zabbix_alarms_per_host=10,
        num_of_instances_per_host=17,
        num_of_ports_per_instance=2,
        num_of_volumes_per_instance=2,
        num_of_vitrage_alarms_per_instance=0,
        num_of_tripleo_controllers=0,
        num_of_zabbix_alarms_per_controller=0).create_graph()

    def get_all(self, datasource_action):
        return self.make_pickleable(self._get_mock_entities(),
                                    MOCK_DATASOURCE,
                                    datasource_action)

    def get_changes(self, datasource_action):
        return self.make_pickleable([],
                                    MOCK_DATASOURCE,
                                    datasource_action)

    def _get_mock_entities(self):
        definitions = json.loads(self.e_graph.json_output_graph())
        for node in definitions['nodes']:
            node[StaticFields.STATIC_ID] = str(node[VProps.GRAPH_INDEX])
            node[StaticFields.TYPE] = node[VProps.VITRAGE_TYPE]
            node[StaticFields.CATEGORY] = node[VProps.VITRAGE_CATEGORY]
            self.delete_fields(node)
        for link in definitions['links']:
            link['source'] = str(link['source'])
            link['target'] = str(link['target'])

        entities = definitions['nodes']
        relationships = definitions['links']
        return self._pack(entities, relationships)

    @staticmethod
    def delete_fields(node):
        if VProps.VITRAGE_ID in node:
            del node[VProps.VITRAGE_ID]
        if VProps.UPDATE_TIMESTAMP in node:
            del node[VProps.UPDATE_TIMESTAMP]
        if VProps.VITRAGE_CATEGORY in node:
            del node[VProps.VITRAGE_CATEGORY]
        if VProps.VITRAGE_OPERATIONAL_STATE in node:
            del node[VProps.VITRAGE_OPERATIONAL_STATE]
        if VProps.VITRAGE_SAMPLE_TIMESTAMP in node:
            del node[VProps.VITRAGE_SAMPLE_TIMESTAMP]
        if VProps.VITRAGE_AGGREGATED_STATE in node:
            del node[VProps.VITRAGE_AGGREGATED_STATE]
        if VProps.VITRAGE_IS_PLACEHOLDER in node:
            del node[VProps.VITRAGE_IS_PLACEHOLDER]
        if VProps.IS_REAL_VITRAGE_ID in node:
            del node[VProps.IS_REAL_VITRAGE_ID]
        if VProps.VITRAGE_IS_DELETED in node:
            del node[VProps.VITRAGE_IS_DELETED]
        if VProps.GRAPH_INDEX in node:
            del node[VProps.GRAPH_INDEX]
        if VProps.VITRAGE_TYPE in node:
            del node[VProps.VITRAGE_TYPE]
