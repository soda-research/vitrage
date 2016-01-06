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
import pecan

from networkx.readwrite import json_graph
from oslo_log import log
from pecan.core import abort
from pecan import rest
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


class TopologyController(rest.RestController):
    @pecan.expose('json')
    def post(self, depth, graph_type, query, root):
        enforce("get topology", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received get topology: depth->%(depth)s '
                     'graph_type->%(graph_type)s root->%(root)s') %
                 {'depth': depth, 'graph_type': graph_type, 'root': root})

        LOG.info(_LI("query is %s") % query)

        return self.get_graph(graph_type)

    @staticmethod
    def get_graph(graph_type):
        # TODO(eyal) temporary mock
        graph_file = pecan.request.cfg.find_file('graph.sample.json')
        try:
            with open(graph_file) as data_file:
                graph = json.load(data_file)
                if graph_type == 'graph':
                    return graph
                if graph_type == 'tree':
                    return json_graph.tree_data(
                        json_graph.node_link_graph(graph).reverse(),
                        root=0)

        except Exception as e:
            LOG.exception("failed to open file ", e)
            abort(404, str(e))
