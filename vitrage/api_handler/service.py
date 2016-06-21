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

import eventlet
from oslo_log import log
import oslo_messaging
from oslo_service import service as os_service

from vitrage.api_handler.apis import EntityGraphApis
from vitrage.api_handler.apis import TemplateApis
from vitrage import messaging
from vitrage import rpc as vitrage_rpc

LOG = log.getLogger(__name__)

eventlet.monkey_patch()


class VitrageApiHandlerService(os_service.Service):

    def __init__(self, conf, e_graph, scenario_repo):
        super(VitrageApiHandlerService, self).__init__()
        self.conf = conf
        self.entity_graph = e_graph
        self.scenario_repo = scenario_repo

    def start(self):
        LOG.info("Vitrage Api Handler Service - Starting...")

        super(VitrageApiHandlerService, self).start()

        transport = messaging.get_transport(self.conf)
        rabbit_hosts = self.conf.oslo_messaging_rabbit.rabbit_hosts
        target = oslo_messaging.Target(topic=self.conf.rpc_topic,
                                       server=rabbit_hosts)

        endpoints = [EntityGraphApis(self.entity_graph),
                     TemplateApis(self.scenario_repo.templates)]

        server = vitrage_rpc.get_server(target, endpoints, transport)

        server.start()

        LOG.info("Vitrage Api Handler Service - Started!")

    def stop(self, graceful=False):
        LOG.info("Vitrage Api Handler Service - Stopping...")

        super(VitrageApiHandlerService, self).stop(graceful)

        LOG.info("Vitrage Api Handler Service - Stopped!")
