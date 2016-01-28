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
    @pecan.expose('json')
    def index(self, entity_id):
        enforce("list alarms", pecan.request.headers,
                pecan.request.enforcer, {})

        LOG.info(_LI('received list alarms with entity  is %s') %
                 entity_id)

        try:
            if mock_file:
                return self.get_mock_alarms()
            else:
                return self.get_alarms(entity_id)
        except Exception as e:
            LOG.exception("failed to get alarms %s", e)
            abort(404, str(e))

    @staticmethod
    def get_mock_alarms():
        # TODO(eyal) temporary mock
        alarms_file = pecan.request.cfg.find_file('alarms.sample.json')
        try:
            with open(alarms_file) as data_file:
                return json.load(data_file)

        except Exception as e:
            LOG.exception("failed to open file ", e)
            abort(404, str(e))

    @staticmethod
    def get_alarms(entity_id):
        return dict()
