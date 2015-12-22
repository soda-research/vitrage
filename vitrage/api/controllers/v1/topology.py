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

from oslo_log import log
from pecan.core import abort
from pecan import rest
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


class TopologyController(rest.RestController):
    @pecan.expose('json')
    def index(self, edges=None, vertices=None, depth=None):

        enforce("get topology", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received get topology: edges->%(edges)s vertices->%('
                     'vertices)s depth->%(depth)s') %
                 {'edges': edges, 'vertices': vertices, 'depth': depth})

        # TODO(eyal) temporary mock
        graph_file = pecan.request.cfg.find_file('graph.sample.json')
        try:
            with open(graph_file) as data_file:
                return json.load(data_file)
        except Exception as e:
            LOG.exception("failed to open file ", e)
            abort(404, str(e))
