# Copyright 2016 - Alcatel-Lucent
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

from networkx.readwrite import json_graph
from oslo_config import cfg
from oslo_log import log
import oslo_messaging
import pecan
from pecan.core import abort
from pecan import rest

from vitrage.api.controllers.v1 import mock_file
from vitrage.api.policy import enforce

# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


def as_tree(graph, root='RESOURCE:node', reverse=False):
    linked_graph = json_graph.node_link_graph(graph)
    if reverse:
        linked_graph = linked_graph.reverse()
    return json_graph.tree_data(linked_graph, root=root)


class TopologyController(rest.RestController):

    def __init__(self):
        transport = oslo_messaging.get_transport(cfg.CONF)
        cfg.CONF.set_override('rpc_backend', 'rabbit')
        target = oslo_messaging.Target(topic='rpcapiv1')
        self.client = oslo_messaging.RPCClient(transport, target)
        self.ctxt = {}

    @pecan.expose('json')
    def post(self, depth, graph_type, query, root):
        enforce("get topology", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received get topology: depth->%(depth)s '
                     'graph_type->%(graph_type)s root->%(root)s') %
                 {'depth': depth, 'graph_type': graph_type, 'root': root})

        LOG.info(_LI("query is %s") % query)

        if mock_file:
            return self.get_mock_graph(graph_type)
        else:
            return self.get_graph(graph_type)

    def get_graph(self, graph_type):
        graph_data = self.client.call(self.ctxt, 'get_topology', arg=None)
        LOG.info(graph_data)

        try:
            graph = json.loads(graph_data)
            if graph_type == 'graph':
                return graph
            if graph_type == 'tree':
                return as_tree(graph)

        except Exception as e:
            LOG.exception("failed to open file %s ", e)
            abort(404, str(e))

    @staticmethod
    def get_mock_graph(graph_type):
        # TODO(eyal) temporary mock
        graph_file = pecan.request.cfg.find_file('graph.sample.json')
        if graph_file is None:
            abort(404, "file graph.sample.json not found")
        try:
            with open(graph_file) as data_file:
                graph = json.load(data_file)
                if graph_type == 'graph':
                    return graph
                if graph_type == 'tree':
                    return as_tree(graph, root=0, reverse=True)

        except Exception as e:
            LOG.exception("failed to open file ", e)
            abort(404, str(e))
