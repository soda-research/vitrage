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

import eventlet
from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import EntityType
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import create_algorithm
from vitrage.graph import Direction
from vitrage import rpc as vitrage_rpc

LOG = log.getLogger(__name__)

eventlet.monkey_patch()


TOPOLOGY_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.RESOURCE}},
        {'==': {VProps.IS_DELETED: False}},
        {
            'or': [
                {'==': {VProps.TYPE: EntityType.OPENSTACK_NODE}},
                {'==': {VProps.TYPE: EntityType.NOVA_ZONE}},
                {'==': {VProps.TYPE: EntityType.NOVA_HOST}},
                {'==': {VProps.TYPE: EntityType.NOVA_INSTANCE}}
            ]
        }
    ]
}

RCA_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
        {'==': {VProps.IS_DELETED: False}}
        ]
}

ALARMS_ALL_QUERY = {
    'and': [
        {'==': {VProps.CATEGORY: EntityCategory.ALARM}},
        {'==': {VProps.IS_DELETED: False}}
    ]
}


class VitrageApiHandlerService(os_service.Service):

    def __init__(self, conf, e_graph):
        super(VitrageApiHandlerService, self).__init__()
        self.conf = conf
        self.entity_graph = e_graph

    def start(self):
        LOG.info("Start VitrageApiHandlerService")

        super(VitrageApiHandlerService, self).start()

        transport = oslo_messaging.get_transport(self.conf)
        rabbit_hosts = self.conf.oslo_messaging_rabbit.rabbit_hosts
        target = oslo_messaging.Target(topic=self.conf.rpc_topic,
                                       server=rabbit_hosts)

        endpoints = [EntityGraphApis(self.entity_graph), ]

        server = vitrage_rpc.get_server(target, endpoints, transport)

        server.start()

        LOG.info("Finish start VitrageApiHandlerService")

    def stop(self, graceful=False):
        LOG.info("Stop VitrageApiHandlerService")

        super(VitrageApiHandlerService, self).stop(graceful)

        LOG.info("Finish stop VitrageApiHandlerService")


class EntityGraphApis(object):
    def __init__(self, entity_graph):
        self.entity_graph = entity_graph

    def get_alarms(self, ctx, arg):
        LOG.info("EntityGraphApis get_alarms arg:%s", str(arg))
        vitrage_id = arg
        if not vitrage_id or vitrage_id == 'all':
            items_list = self.entity_graph.get_vertices(
                query_dict=ALARMS_ALL_QUERY)
        else:
            items_list = self.entity_graph.neighbors(
                vitrage_id,
                vertex_attr_filter={VProps.CATEGORY: EntityCategory.ALARM,
                                    VProps.IS_DELETED: False})

        # TODO(alexey) this should not be here, but in the transformer
        modified_alarms = self._add_resource_details_to_alarms(items_list)

        LOG.info("EntityGraphApis get_alarms result:%s", str(modified_alarms))
        return json.dumps({'alarms': [v.properties for v in modified_alarms]})

    def get_topology(self, ctx, graph_type, depth, query, root):
        found_graph = self._get_topology(ctx, graph_type, query, root, depth)
        return found_graph.output_graph()

    def get_rca(self, ctx, root):
        ga = create_algorithm(self.entity_graph)
        found_graph = ga.graph_query_vertices(
            query_dict=RCA_QUERY,
            root_id=root)
        found_graph.inspected_index = self._find_rca_index(found_graph, root)
        json_graph = found_graph.output_graph()
        return json_graph

    def _get_topology(self, ctx, graph_type, query, root, depth=None):
        ga = create_algorithm(self.entity_graph)
        if graph_type == 'tree':
            final_query = query if query else TOPOLOGY_QUERY
        else:
            final_query = {}
        return ga.graph_query_vertices(
            query_dict=final_query,
            root_id=root)

    @staticmethod
    def _get_first(lst):
        if len(lst) == 1:
            return lst[0]
        else:
            raise ValueError('Alarm has ' + str(len(lst)) +
                             ' connected resources (expected 1).')

    def _add_resource_details_to_alarms(self, alarms):
        incorrect_alarms = []
        for alarm in alarms:
            try:
                resources = self.entity_graph.neighbors(
                    v_id=alarm.vertex_id,
                    edge_attr_filter={EProps.RELATIONSHIP_TYPE: EdgeLabels.ON},
                    direction=Direction.OUT)

                resource = self._get_first(resources)
                alarm["resource_id"] = resource.get(VProps.ID, '')
                alarm["resource_type"] = resource.get(VProps.TYPE, '')
            except ValueError as ve:
                incorrect_alarms.append(alarm)
                LOG.error('Alarm %s\nException %s', alarm, ve)

        return [item for item in alarms if item not in incorrect_alarms]

    @staticmethod
    def _find_rca_index(found_graph, root):
        root_index = 0
        for vertex in found_graph._g:
            if vertex == root:
                break
            root_index += 1
        return root_index
