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
from oslo_config import cfg
import oslo_messaging
import pecan

from oslo_log import log
from pecan.core import abort
from pecan import rest

from vitrage.api.controllers.v1 import mock_file
from vitrage.api.policy import enforce
# noinspection PyProtectedMember
from vitrage.i18n import _LI

LOG = log.getLogger(__name__)


class AlarmsController(rest.RestController):

    def __init__(self):
        transport = oslo_messaging.get_transport(cfg.CONF)
        cfg.CONF.set_override('rpc_backend', 'rabbit')
        target = oslo_messaging.Target(topic='rpcapiv1')
        self.client = oslo_messaging.RPCClient(transport, target)
        self.ctxt = {}

    @pecan.expose('json')
    def index(self, vitrage_id=None):
        return self.post(vitrage_id)

    @pecan.expose('json')
    def post(self, vitrage_id):
        enforce("list alarms", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received list alarms with vitrage id %s') %
                 vitrage_id)

        try:
            if mock_file:
                return self.get_mock_alarms()
            else:
                return self.get_alarms(vitrage_id)
        except Exception as e:
            LOG.exception("failed to get alarms %s", e)
            abort(404, str(e))

    @staticmethod
    def get_mock_alarms():
        # TODO(eyal) temporary mock
        alarms_file = pecan.request.cfg.find_file('alarms.sample.json')
        if alarms_file is None:
            abort(404, "file alarms.sample.json not found")
        try:
            with open(alarms_file) as data_file:
                return json.load(data_file)['alarms']

        except Exception as e:
            LOG.exception("failed to open file %s", e)
            abort(404, str(e))

    def get_alarms(self, vitrage_id=None):
        alarms_json = self.client.call(self.ctxt, 'get_alarms', arg=vitrage_id)
        LOG.info(alarms_json)

        try:
            alarms_list = json.loads(alarms_json)['alarms']
            return alarms_list

        except Exception as e:
            LOG.exception("failed to open file %s ", e)
            abort(404, str(e))
