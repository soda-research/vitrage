# Copyright 2016 - Nokia Corporation
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

import oslo_messaging
import pecan

from oslo_config import cfg
from oslo_log import log
from pecan.core import abort
from pecan import rest
from vitrage.api.controllers.v1 import mock_file
from vitrage.api.policy import enforce

# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


class RCAController(rest.RestController):

    def __init__(self):
        transport = oslo_messaging.get_transport(cfg.CONF)
        cfg.CONF.set_override('rpc_backend', 'rabbit')
        target = oslo_messaging.Target(topic='rpcapiv1')
        self.client = oslo_messaging.RPCClient(transport, target)
        self.ctxt = {}

    @pecan.expose('json')
    def get(self, alarm_id):
        enforce('get rca', pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received show rca with alarm id %s') % alarm_id)
        if mock_file:
            return self.get_mock_graph()
        else:
            return self.get_rca(alarm_id)

    def get_rca(self, alarm_id):

        try:
            graph_data = self.client.call(self.ctxt, 'get_rca', root=alarm_id)
            LOG.info(graph_data)
            graph = json.loads(graph_data)
            return graph

        except Exception as e:
            LOG.exception('failed to get rca %s ', e)
            abort(404, str(e))

    @staticmethod
    def get_mock_graph():
        file_name = 'rca.sample.json'
        graph_file = pecan.request.cfg.find_file(file_name)
        if graph_file is None:
            abort(404, 'file %s not found' % file_name)
        try:
            with open(graph_file) as data_file:
                graph = json.load(data_file)
                return graph

        except Exception as e:
            LOG.exception('failed to open file %s', e)
            abort(404, str(e))
