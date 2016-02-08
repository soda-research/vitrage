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

import pecan

from oslo_log import log
from pecan import redirect
from pecan import rest
from six.moves import urllib
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


class RCAController(rest.RestController):
    @pecan.expose('json')
    def get(self, alarm_id):
        enforce('get rca', pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received show rca with alarm id %s') %
                 alarm_id)
        params = urllib.parse.urlencode(dict(query=None, root=alarm_id,
                                             graph_type='graph'))
        redirect('/v1/topology?' + params, internal=True)
