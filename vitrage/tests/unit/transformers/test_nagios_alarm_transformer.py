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
from oslo_log import log as logging

from vitrage.common.constants import EntityType
from vitrage.entity_graph.transformer.plugins.nagios import NagiosAlarm
from vitrage.entity_graph.transformer.plugins.nova.host import Host
from vitrage.tests import base
from vitrage.tests.mocks import mock_syncronizer as mock_sync


LOG = logging.getLogger(__name__)


class NagiosTransformerTest(base.BaseTest):

    def setUp(self):
        super(NagiosTransformerTest, self).setUp()

        self.transformers = {}
        host_transformer = Host(self.transformers)
        self.transformers[EntityType.NOVA_HOST] = host_transformer

    def test_nagios_alarm_transform(self):
        LOG.debug('Nagios alarm transformer test: transform entity event')

        # Test setup
        spec_list = mock_sync.simple_nagios_alarm_generators(host_num=4,
                                                             events_num=4)
        nagios_alarms = mock_sync.generate_sequential_events_list(spec_list)

        # Test action
        for alarm in nagios_alarms:
            NagiosAlarm(self.transformers)._create_entity_vertex(alarm)
