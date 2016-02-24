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
import traceback

import eventlet
from oslo_config import cfg
from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service

from vitrage.common.constants import EdgeLabels
from vitrage.common.constants import EdgeProperties as EProps
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.graph import create_algorithm
from vitrage.graph import Direction

LOG = log.getLogger(__name__)

eventlet.monkey_patch()


class VitrageApiHandlerService(os_service.Service):

    def __init__(self, e_graph):
        super(VitrageApiHandlerService, self).__init__()
        self.entity_graph = e_graph

    def start(self):
        LOG.info("Start VitrageApiHandlerService")

        super(VitrageApiHandlerService, self).start()

        transport = oslo_messaging.get_transport(cfg.CONF)

        # TODO(Dany) add real server
        target = oslo_messaging.Target(topic='rpcapiv1', server='localhost')

        # TODO(Dany) add rabbit configuratipn
        # target = om.Target(topic='testme', server='192.168.56.102')
        # target = oslo_messaging.Target(
        #     topic='testme', server='135.248.18.223')
        # cfg.CONF.set_override('rabbit_host', '135.248.18.223')
        # cfg.CONF.set_override('rabbit_port', 5672)
        # cfg.CONF.set_override('rabbit_userid', 'guest')
        # cfg.CONF.set_override('rabbit_password', 'cloud')
        # cfg.CONF.set_override('rabbit_login_method', 'AMQPLAIN')
        # cfg.CONF.set_override('rabbit_virtual_host', '/')
        cfg.CONF.set_override('rpc_backend', 'rabbit')

        endpoints = [EntityGraphApis(self.entity_graph), ]

        # TODO(Dany) use eventlet instead of threading
        server = oslo_messaging.get_rpc_server(transport, target,
                                               endpoints, executor='eventlet')

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
                {VProps.CATEGORY: EntityCategory.ALARM})
        else:
            items_list = self.entity_graph.neighbors(
                vitrage_id,
                vertex_attr_filter={VProps.CATEGORY: EntityCategory.ALARM})

        # TODO(alexey) this should not be here, but in the transformer
        modified_alarms = self._add_resource_details_to_alarms(items_list)

        LOG.info("EntityGraphApis get_alarms result:%s", str(modified_alarms))
        return json.dumps({'alarms': [v.properties for v in modified_alarms]})

    def get_topology(self, ctx, graph_type, depth, query, root):
        ga = create_algorithm(self.entity_graph)
        query = query if query else \
            {'!=': {VProps.CATEGORY: EntityCategory.ALARM}}
        found_graph = ga.graph_query_vertices(
            query_dict=query,
            root_id=root)
        return found_graph.output_graph()

    @staticmethod
    def _get_first(lst):
        if len(lst) == 1:
            return lst[0]
        else:
            raise ValueError("Incorrect number of items in lst: %s.\n "
                             "Exception: %s", lst, traceback.print_exc())

    def _add_resource_details_to_alarms(self, alarms):
        incorrect_alarms = []
        for alarm in alarms:
            try:
                resources = self.entity_graph.neighbors(
                    v_id=alarm.vertex_id,
                    edge_attr_filter={EProps.RELATIONSHIP_NAME: EdgeLabels.ON},
                    direction=Direction.OUT)

                resource = self._get_first(resources)
                alarm["resource_id"] = resource.get(VProps.ID, '')
                alarm["resource_type"] = resource.get(VProps.TYPE, '')
            except ValueError as ve:
                incorrect_alarms.append(alarm)
                LOG.error(ve)

        return [item for item in alarms if item not in incorrect_alarms]
